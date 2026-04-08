import os
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime

def update_index():
    files = [f for f in os.listdir('.') if f.endswith('.html') and f != 'index.html']
    report_data = []
    
    date_pattern = re.compile(r'(202\d[\.\-]\d{2}[\.\-]\d{2})')
    # 영문 티커(미국주식) 또는 6자리 숫자(한국 종목코드) + 코스피/코스닥 한글 표기 대응
    market_pattern = re.compile(r'([A-Z]{1,6}\s*[\/\|]?\s*(?:NASDAQ|NYSE|AMEX)|\b\d{6}\b(?:\s*[\/\|]?\s*(?:KOSPI|KOSDAQ|코스피|코스닥))?)', re.IGNORECASE)

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            
            # 1. 제목 추출: 파일명을 그대로 사용하여 가장 정확하게 표시 (예: "LS ELECTRIC.html" -> "LS ELECTRIC")
            title = file.replace('.html', '')
            
            # 2. 요약 추출
            summary_tag = soup.find('p', class_=re.compile("text-xl"))
            summary = summary_tag.text.strip().split('\n')[0] if summary_tag else "요약 정보가 없습니다."
            
            # 본문 분리 (빈 줄 제외)
            body_element = soup.body if soup.body else soup
            raw_lines = [line.strip() for line in body_element.get_text(separator='\n').split('\n') if line.strip()]
            
            date_str = ""
            sector_str = "리포트"
            market_str = "Market 정보"

            # 3. 날짜, 섹터, 종목코드 추출
            for i, line in enumerate(raw_lines):
                # 날짜 및 섹터 찾기
                if not date_str:
                    date_match = date_pattern.search(line)
                    if date_match:
                        date_str = date_match.group(1)
                        
                        # 섹터 찾기: 날짜 위쪽 라인 탐색
                        for j in range(i-1, -1, -1):
                            candidate = raw_lines[j].strip()
                            # 20자 이내, 제목과 다르고, 연도/종목코드 같은 4자리 이상 숫자가 없는 문자열 (2차전지 등은 허용)
                            if candidate and len(candidate) <= 20 and candidate != title and not re.search(r'\d{4}', candidate):
                                # 불필요한 기본 문구 제외
                                if '리서치' not in candidate and '프레젠테이션' not in candidate and 'wal!street' not in candidate.lower():
                                    sector_str = candidate
                                    break
                
                # 종목코드 찾기
                if market_str == "Market 정보":
                    market_match = market_pattern.search(line)
                    if market_match:
                        # 추출 후 공백 정리 및 대문자화, 코스피/코스닥 한글을 영문으로 통일
                        raw_market = re.sub(r'\s+', ' ', market_match.group(1)).upper()
                        market_str = raw_market.replace('코스피', 'KOSPI').replace('코스닥', 'KOSDAQ')

            if not date_str:
                mtime = os.path.getmtime(file)
                date_str = datetime.fromtimestamp(mtime).strftime('%Y.%m.%d')
            
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
