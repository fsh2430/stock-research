import os
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime

def update_index():
    # 폴더 내 모든 html 파일 스캔 (index.html 제외)
    files = [f for f in os.listdir('.') if f.endswith('.html') and f != 'index.html']
    
    report_data = []
    
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            
            # 문서 내에서 제목(title)과 요약문 추출
            title_tag = soup.find('title')
            title = title_tag.text.split(' ')[0] if title_tag else file.replace('.html', '')
            
            # 본문의 첫 번째 주요 설명 단락을 요약으로 활용
            summary_tag = soup.find('p', class_=re.compile("text-xl"))
            summary = summary_tag.text.strip().split('\n')[0] if summary_tag else ""
            
            # 파일이 수정된 날짜를 가져와서 date에 입력 (오늘 날짜)
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            report_data.append({
                "id": file,
                "sector": "리포트",
                "date": today_date,
                "title": title,
                "market": "Market",
                "summary": summary
            })

    # index.html 읽어오기
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 추출한 데이터를 JSON 문자열로 변환
    json_data = json.dumps(report_data, ensure_ascii=False, indent=12)
    
    # 정규식을 이용해 기존 reportData 배열 부분을 자동 생성된 데이터로 교체
    pattern = re.compile(r'const reportData = \[.*?\];', re.DOTALL)
    new_script = f"const reportData = {json_data};"
    updated_html = pattern.sub(new_script, html_content)

    # index.html 업데이트 
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(updated_html)
        
    print(f"{len(report_data)}개의 리포트가 성공적으로 업데이트되었습니다.")

if __name__ == '__main__':
    update_index()
