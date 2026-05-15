import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


URLS = {
    "stats": "https://fbref.com/en/comps/9/stats/Premier-League-Stats",
    "keepers": "https://fbref.com/en/comps/9/keepers/Premier-League-Stats",
    "shooting": "https://fbref.com/en/comps/9/shooting/Premier-League-Stats",
    "playingtime": "https://fbref.com/en/comps/9/playingtime/Premier-League-Stats",
    "miscellaneous": "https://fbref.com/en/comps/9/misc/Premier-League-Stats"
}

# Folder lưu file CSV.
# Với cách này, folder raw_table_csv sẽ nằm cùng thư mục với file .py này.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "data")


def flatten_columns(df):
    """
    FBRef thường có bảng nhiều tầng header.
    Hàm này giúp gộp header nhiều tầng thành tên cột 1 dòng để lưu CSV dễ đọc hơn.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(col) for col in cols if str(col) != "nan" and "Unnamed" not in str(col)]).strip()
            for cols in df.columns
        ]
    else:
        df.columns = [str(col).strip() for col in df.columns]

    return df


def save_table_to_csv(table, name):
    """
    Convert HTML table sang DataFrame rồi lưu thành file CSV.
    """
    df = pd.read_html(str(table))[0]
    df = flatten_columns(df)

    output_file = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"Đã lưu dữ liệu CSV vào: {output_file}")
    print(f"Số dòng dữ liệu: {len(df)}")
    print(f"Số cột dữ liệu: {len(df.columns)}")


def crawl_fbref_test():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Folder lưu file CSV là:", OUTPUT_DIR)

    print("Đang khởi tạo trình duyệt Selenium...")
    chrome_options = Options()

    # Nếu muốn chạy ẩn trình duyệt thì bỏ dấu # ở dòng dưới:
    # chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = None

    try:
        driver = webdriver.Chrome(options=chrome_options)

        for i, (name, url) in enumerate(URLS.items()):
            print(f"\n[{name.upper()}] Đang mở trang: {url}")
            driver.get(url)

            # Link đầu tiên chờ lâu hơn để vượt Cloudflare / tải trang ban đầu.
            if i == 0:
                print("Đợi 5 giây ở lần đầu để trang tải xong...")
                time.sleep(5)
            else:
                print("Đợi 2 giây để JavaScript render bảng...")
                time.sleep(2)

            html_content = driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")

            # Tìm class "table_container" và lấy bảng ở phần tử thứ 3, index = 2.
            containers = soup.find_all(class_="table_container")

            table = None
            if len(containers) >= 3:
                table = containers[2].find("table")

            if table:
                print(f"[THÀNH CÔNG] Đã lọc được bảng của {name}!")

                # Loại bỏ các hàng header lặp lại trong thân bảng.
                for thead_row in table.find_all("tr", class_="thead"):
                    thead_row.decompose()

                rows = table.find_all("tr")
                print(f"Tổng số lượng hàng <tr> trích xuất được: {len(rows)}")

                save_table_to_csv(table, name)
            else:
                print(f"[LỖI] Không tìm thấy bảng trên trang {name}!")
                print(f"Số lượng table_container tìm được: {len(containers)}")

            # Nghỉ trước khi quét link tiếp theo để hạn chế bị FBRef chặn request.
            time.sleep(2)

    except Exception as e:
        print(f"Lỗi khi chạy Selenium: {e}")

    finally:
        print("\nHoàn tất quá trình cào dữ liệu. Tắt trình duyệt.")
        if driver:
            driver.quit()


if __name__ == "__main__":
    crawl_fbref_test()
