import os
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime

def update_index():
    files = [f for f in os.listdir('.') if f.endswith('.html') and f != 'index.html']
    report_data = []
    
    # 정규식 패턴 (날짜 및 마켓/코드)
    date_pattern = re.compile(r'(202\d[\.\-]\d{2}[\.\-]\d{2})')
    # 코드와 KOSPI/KOSDAQ 사이에 공백이나 기호(|, /)가 있어도 찾을 수 있도록 개선
    market_pattern = re.compile(r'([A-Z0-9]{4,6}\s*[\/\|]?\s*(?:KOSPI|KOSDAQ|NASDAQ|NYSE|AMEX))', re.IGNORECASE)

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            
            # 1. 제목 추출 (띄어쓰기로 자르지 않고 불필요한 뒷말만 제거)
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.text.replace('심층 리서치 프레젠테이션', '').strip()
            else:
                title = file.replace('.html', '')
            
            # 요약 추출
            summary_tag = soup.find('p', class_=re.compile("text-xl"))
            summary = summary_tag.text.strip().split('\n')[0] if summary_tag else "요약 정보가 없습니다."
            
            # HTML 본문 텍스트를 줄바꿈 기준으로 분리 (빈 줄 제거)
            body_element = soup.body if soup.body else soup
            raw_lines = [line.strip() for line in body_element.get_text(separator='\n').split('\n') if line.strip()]
            
            date_str = ""
            sector_str = "리포트"
            market_str = "Market 정보"

            # 2. 날짜 및 섹터 추출
            for i, line in enumerate(raw_lines):
                date_match = date_pattern.search(line)
                if date_match:
                    date_str = date_match.group(1)
                    
                    # 섹터 찾기: 날짜가 있는 곳에서 위쪽으로 거슬러 올라가며 찾음
                    for j in range(i-1, -1, -1):
                        candidate = raw_lines[j]
                        # 15자 이내의 짧은 단어이고, 제목과 똑같지 않으며 숫자가 아닌 것을 섹터로 간주
                        if 0 < len(candidate) <= 15 and candidate not in title and not candidate.isnumeric():
                            sector_str = candidate
                            break
                    break
            
            # 날짜가 없으면 파일 업로드 날짜 사용
            if not date_str:
                mtime = os.path.getmtime(file)
                date_str = datetime.fromtimestamp(mtime).strftime('%Y.%m.%d')

            # 3. 마켓 및 종목코드 추출
            for line in raw_lines:
                market_match = market_pattern.search(line)
                if market_match:
                    market_str = market_match.group(1).upper()
                    break
            
            report_data.append({
                "id": file,
                "sector": sector_str,
                "date": date_str,
                "title": title,
                "market": market_str,
                "summary": summary
            })

    # 날짜 최신순 정렬
    report_data.sort(key=lambda x: x['date'], reverse=True)

    # index.html 업데이트
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    json_data = json.dumps(report_data, ensure_ascii=False, indent=12)
    pattern = re.compile(r'const reportData = \[.*?\];', re.DOTALL)
    new_script = f"const reportData = {json_data};"
    updated_html = pattern.sub(new_script, html_content)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(updated_html)
        
    print(f"{len(report_data)}개의 리포트가 성공적으로 업데이트되었습니다.")

if __name__ == '__main__':
    update_index()
