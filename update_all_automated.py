import os
import re
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup

# 設定
HTML_PATH = '/home/ubuntu/index.html'
TIMEZONE_OFFSET = 9  # JST

def get_now_jst():
    from datetime import timezone, timedelta
    return datetime.now(timezone(timedelta(hours=TIMEZONE_OFFSET)))

async def fetch_pref_projects():
    """徳島県の入札情報を取得（簡易版）"""
    projects = []
    try:
        url = "https://e-denshinyusatsu.pref.tokushima.lg.jp/archives/category/order"
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 建築関連のキーワード
        keywords = ["建築", "営繕", "校舎", "庁舎", "体育館", "住宅"]
        
        articles = soup.find_all('article')
        for article in articles[:10]:
            title_elem = article.find('h2')
            date_elem = article.find('time')
            if title_elem and date_elem:
                title = title_elem.get_text(strip=True)
                date = date_elem.get_text(strip=True)
                
                if any(k in title for k in keywords):
                    advice = "大規模建築。杭工事（ハイパーメガ工法等）の提案が有効。" if "改築" in title or "新築" in title else "地盤改良（ウルトラコラム工法）の検討対象。"
                    projects.append({
                        "title": title,
                        "date": date,
                        "advice": advice
                    })
    except Exception as e:
        print(f"Error fetching pref projects: {e}")
    
    return projects

async def update_html(projects):
    """HTMLファイルを更新"""
    if not os.path.exists(HTML_PATH):
        print(f"Error: {HTML_PATH} not found.")
        return

    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 最終取得日の更新
    now = get_now_jst()
    date_str = now.strftime('%Y/%m/%d %H:%M')
    content = re.sub(r'最終取得日: \d{4}/\d{2}/\d{2}( \d{2}:\d{2})?', f'最終取得日: {date_str}', content)

    # プロジェクトリストの生成
    rows = ""
    for p in projects:
        rows += f"""
                        <tr>
                            <td class="py-4 px-6">
                                <span class="municipality-tag">自動取得</span>
                                <div class="font-bold text-slate-800 mt-1">{p['title']}</div>
                            </td>
                            <td class="py-4 px-6 text-slate-500 text-xs">{p['date']}</td>
                            <td class="py-4 px-6"><div class="bg-blue-50 text-blue-700 p-2 rounded-lg text-[11px]">{p['advice']}</div></td>
                        </tr>"""

    # プレースホルダー間の置換
    pattern = re.compile(r'<!-- PREF_PROJECTS_START -->.*?<!-- PREF_PROJECTS_END -->', re.DOTALL)
    replacement = f'<!-- PREF_PROJECTS_START -->{rows}\n                        <!-- PREF_PROJECTS_END -->'
    new_content = pattern.sub(replacement, content)

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Successfully updated {HTML_PATH} with {len(projects)} projects.")

async def main():
    # 1. 徳島県の案件を取得
    pref_projects = await fetch_pref_projects()
    
    # 2. HTMLを更新
    await update_html(pref_projects)

if __name__ == "__main__":
    asyncio.run(main())
