import os
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime

def update_index():
    files = [f for f in os.listdir('.') if f.endswith('.html') and f != 'index.html']
    report_data = []
    
    # 찾을 패턴 미리 설정 (날짜, 마켓/종목코드)
    date_pattern = re.compile(r'(202\d[\.\-]\d{2}[\.\-]\d{2})')
    market_pattern = re.compile(r'([A-Z0-9]{1,6}\s+(?:KOSPI|KOSDAQ|NASDAQ|NYSE|AMEX))', re.IGNORECASE)

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            
            # 제목 추출
            title_tag = soup.find('title')
            title = title_tag.text.split(' ')[0] if title_tag else file.replace('.html', '')
            
            # 요약 추출
            summary_tag = soup.find('p', class_=re.compile("text-xl"))
            summary = summary_tag.text.strip().split('\n')[0] if summary_tag else ""
            
            # HTML 본문 텍스트를 줄바꿈 기준으로 분리
            body_element = soup.body if soup.body else soup
            raw_lines = [line.strip() for line in body_element.get_text(separator='\n').split('\n') if line.strip()]
            
            # 기본값 설정
            date_str = ""
            sector_str = "리포트"
            market_str = "Market 정보"

            # 1. 날짜 & 섹터 동시 추출
            for i, line in enumerate(raw_lines):
                date_match = date_pattern.search(line)
                if date_match:
                    date_str = date_match.group(1) # 예: 2024.12.19
                    
                    # 섹터는 화면 구조상 보통 날짜 바로 윗줄에 있음
                    if i > 0:
                        sector_candidate = raw_lines[i-1]
                        # 윗줄이 너무 긴 문장이면 섹터가 아니라고 판단 (20자 이내만 허용)
                        if len(sector_candidate) < 20: 
                            sector_str = sector_candidate
                    break
            
            # 본문에 날짜가 적혀있지 않으면 파일 업로드/수정 날짜를 대신 사용
            if not date_str:
                mtime = os.path.getmtime(file)
                date_str = datetime.fromtimestamp(mtime).strftime('%Y.%m.%d')

            # 2. 마켓 및 종목코드 추출 (예: 066570 KOSPI)
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

    # 추출된 리포트들을 '날짜 최신순(내림차순)'으로 보기 좋게 정렬
    report_data.sort(key=lambda x: x['date'], reverse=True)

    # index.html 파일 업데이트
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
