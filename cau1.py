import pandas as pd
from DrissionPage import ChromiumPage
import os
import time
from io import StringIO

def _flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            str(col[1]).strip() if 'Unnamed' in str(col[0])
            else f"{col[0]}_{col[1]}".strip()
            for col in df.columns.values
        ]
    else:
        df.columns = [str(col).strip() for col in df.columns]
    return df


def crawl_epl_direct():
    if not os.path.exists('data'):
        os.makedirs('data')

    print("Dang khoi dong DrissionPage...")
    page = ChromiumPage()
    
    try:
        url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
        print(f"Dang truy cap: {url}")
        page.get(url)
        
        for attempt in range(1, 4):
            print(f"Tim kiem bang du lieu (lan {attempt}/3)...")
            if page.ele('tag:table', timeout=60):
                print("Da thay bang du lieu tren web.")
                break
            if attempt < 3:
                print(f"Khong tim thay bang, thu lai sau 5 giay...")
                time.sleep(5)
        else:
            raise RuntimeError(
                "Khong tim thay bang du lieu tren trang sau 3 lan thu. "
                "Kiem tra ket noi mang hoac URL co the da thay doi."
            )

        time.sleep(3) 
        html_source = page.html
        
        print("Dang doc HTML...")
        tables = pd.read_html(StringIO(html_source))
        print(f"Tim thay tong cong {len(tables)} bang tren trang web.")
        
        df = None
        for i, t in enumerate(tables):
            col_names = [str(c) for c in t.columns.values]
            if any('Player' in name for name in col_names):
                df = t
                print(f"Da xac dinh duoc bang chua cau thu (Bang so {i+1}).")
                break
                
        if df is None:
            print("Loi: Khong co bang nao chua cot 'Player'.")
            return

        print("Dang lam sach du lieu...")
        df = _flatten_columns(df)

        min_col = None
        for col in df.columns:
            if 'Min' in col:
                min_col = col
                break
        
        if min_col is None:
            print("Loi: Khong tim thay cot phut thi dau.")
            return

        df = df[df['Player'] != 'Player'] 
        df[min_col] = pd.to_numeric(df[min_col], errors='coerce')
        df_filtered = df[df[min_col] > 90].copy()
        
        df_filtered.fillna('N/a', inplace=True)
        df_filtered.rename(columns={min_col: 'Min'}, inplace=True)
        
        df_filtered.reset_index(drop=True, inplace=True)
        df_filtered.index += 1
        df_filtered.index.name = 'STT'
        
        save_path = os.path.join(os.getcwd(), 'data', 'epl_players_25_26.csv')
        df_filtered.to_csv(save_path, index=True, encoding='utf-8')
        print(f"Thanh cong! Da luu file CSV tai duong dan:\n{save_path}")
        
    except Exception as e:
        print(f"Co loi xay ra o khau xu ly du lieu: {e}")
    finally:
        print("Dang dong trinh duyet...")
        page.quit()

if __name__ == "__main__":
    crawl_epl_direct()