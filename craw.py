import re
import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import unquote
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
import mistune
import markdown
import webbrowser
import concurrent.futures
import unittest

db_file = 'database/problem.db'
class HTMLRenderer(mistune.HTMLRenderer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def block_code(self, code, lang=None):
        if lang:
            code = mistune.escape(code)
            return f'<pre><code class="{lang}">{code}</code></pre>\n'
        return f'<pre><code>{mistune.escape(code)}</code></pre>\n'

class TestCreateDirectory(unittest.TestCase):
    def test_create_directory(self):
        tag_name = '提高+_省选−_各省省选_湖南_2001'
        directory_name = '2222 [HNOI2001]_矩阵乘积'
        expected_result = 'data\\提高+_省选−_各省省选_湖南_2001\\2222 [HNOI2001]_矩阵乘积'
        
        directory_path = create_directory(tag_name, directory_name)
        
        self.assertEqual(directory_path, expected_result)
        self.assertTrue(os.path.exists(directory_path))
        print("测试通过")

# 连接SQLite数据库，如果数据库不存在则会自动创建
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 创建problem_table表格
cursor.execute('''CREATE TABLE IF NOT EXISTS problem_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_id INTEGER,
                    problem_title TEXT,
                    difficulty TEXT,
                    tags TEXT,
                    file_path TEXT)''')

# 提交更改并关闭数据库连接
conn.commit()
conn.close()

base_url = "https://www.luogu.com.cn/problem/P"
base_urls = "https://www.luogu.com.cn/problem/solution/P"
save_path = "data"
path = "abc"
def validate_input():
    try:
        minn = int(start_entry.get())
        maxn = int(end_entry.get())
        sum = int(total_entry.get())
        
        if minn < 1000 or minn > 9639 or maxn < 1000 or maxn > 9639 or minn > maxn or sum <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("输入错误", "请输入1000到9639间的整数作为号数,并确保开始号数小于等于终止号数，总数不为负数")
        return False
    
    return True
def main():
    if not validate_input():
        return
    minn = int(start_entry.get())
    maxn = int(end_entry.get())
    sum = int(total_entry.get())
    counter = 0
    print("计划爬取到P{}".format(maxn))
    with ThreadPoolExecutor(max_workers=6) as executor:  # 设置线程池最大线程数
        futures = []
        for i in range(minn, maxn+1):
            future = executor.submit(crawl_problem, i)
            futures.append(future)
            counter += 1
            if counter >= sum:
                break
        # 等待所有任务完成
        concurrent.futures.wait(futures)
    print("爬取完毕")

def crawl_problem(i):
    print("正在爬取P{}...\n".format(i), end="")
    problem_url = base_url + str(i)

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # 检查是否存在相同的 problem_id
    cursor.execute(f"SELECT * FROM problem_table WHERE problem_id={i}")
    existing_data = cursor.fetchone()

    if existing_data:
        print("P{}题已存在".format(i))
        conn.close()
        return
    else:
        problem_html = get_html(problem_url)
        if problem_html is None:
            print("P{}爬取失败，可能是不存在该题或无权查看".format(i))
            conn.close()
        else:
            problem_title, problem_text = parse_problem_html(problem_html)
            print("P{}爬取成功！正在保存...\n".format(i), end="")
            difficulty,tags,folder_name = get_tag(i)

            problem_directory = create_directory(folder_name, str(i) + ' ' + problem_title)
            print(problem_directory)
            save_data(problem_text, "p{}-".format(i) + problem_title + ".md", problem_directory)
            cursor.execute("INSERT INTO problem_table (problem_id, problem_title, difficulty, tags, file_path) VALUES (?, ?, ?, ?, ?)",
                   (i, problem_title, difficulty, tags, problem_directory))

            # 提交更改并关闭数据库连接
            conn.commit()
            # 关闭数据库连接
            conn.close()
            solution_url = base_urls + str(i)
            get_sol(solution_url, i, problem_title, problem_directory)


def get_html(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        #print(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        head = soup.find('head')
        title = head.find('title').string.strip()
        if title == "出错了 - 洛谷":
            return None
        else:
            return response.text
    except requests.exceptions.RequestException as e:
        return None
    
def get_sol(url,i,problem_title,problem_directory):
    headers = {
      "Cookie": '__client_id=4309367d9ac6b47f41df97c6121a5c33b5aef9a9;_uid=790971;',
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
    }
    response = requests.get(url, headers=headers)
    html_content = response.text
    pattern = r'decodeURIComponent\("([^"]+)"\)'
    result = re.search(pattern, html_content)
    if result:
        target_string = result.group(1)

    decoded_string = unquote(target_string)
    decoded_data = json.loads(decoded_string)
    try:
        content = decoded_data['currentData']['solutions']['result'][0]['content']
        print("P{}题解爬取成功！正在保存...".format(i), end="")
        save_data(content, "P{}-".format(i) + problem_title + "-题解.md",problem_directory)
        print("保存成功!")
    except:
        print("P{}没有找到题解".format(i)) 
   
def get_tag(i):
    url = base_url + str(i)
    options = Options()
    options.add_argument('-headless')  # 设置为无头模式
    browser = webdriver.Firefox(options=options)
    browser.get(url)
    button = browser.find_element(By.CSS_SELECTOR, value='div.card:nth-child(2) > div:nth-child(3) > span:nth-child(1)')
    button.click()
    tags = browser.find_element(By.CSS_SELECTOR, value='.tags-wrap').text
    difficult = browser.find_element(By.CSS_SELECTOR, value='.info-rows > div:nth-child(2) > span:nth-child(2) > a:nth-child(1) > span:nth-child(1)').text
    browser.quit()
    # 提取标签名称
    folder_name = ''.join([elem.replace('/', '_') for elem in difficult]) + '_' + ''.join([elem.replace('\n', '_').replace("\\", "_") for elem in tags])
    return difficult,tags,folder_name

def parse_problem_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    core = soup.find('article')
    
    title = core.find('h1').string.strip()
    content = str(core)

    content = re.sub(r"<h1>", "# ", content)
    content = re.sub(r"<h2>", "## ", content)
    content = re.sub(r"<h3>", "### ", content)
    content = re.sub(r"</?[a-zA-Z]+[^<>]*>", "", content)
    title = re.sub(r'[\/:*?"<>|]', '', title)
    
    # 替换空格为下划线
    title = title.replace(' ', '_')
    return title, content

def save_data(data, filename, directory):
    filepath = os.path.join(directory, filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(data)

def create_directory(tag_name,directory_name):
    directory_path = os.path.join(save_path,tag_name, directory_name)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path
def query():
     # 数据库连接
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # 查询语句
    query_sql = "SELECT * FROM problem_table WHERE 1=1"
    if difficulty_var.get():
        query_sql += " AND difficulty='" + difficulty_var.get() + "'"
    # 获取输入的标签并拆分为列表
    tags_input = tags_var.get().split()
    if tags_input:
        for tag in tags_input:
            query_sql += f" AND tags LIKE '%{tag}%'"

    if problem_id_var.get():
        query_sql += " AND problem_id=" + problem_id_var.get()
    if problem_title_var.get():
        query_sql += " AND problem_title LIKE '%" + problem_title_var.get() + "%'"

    # 执行查询
    cursor.execute(query_sql)
    result = cursor.fetchall()

     # 格式化查询结果
    formatted_result = []
    for row in result:
        problem_id = row[1]
        problem_title = row[2]
        difficulty = row[3]
        tags = row[4].replace('\n', ';')
        path = row[5]
        formatted_result.append(f"题号：{problem_id}\n题目：{problem_title}\n难度：{difficulty}\n标签：{tags}\n点击下方路径打开题目文件夹：\n{path}\n\n")

    # 显示查询结果
    result_text.config(state='normal')
    result_text.delete('1.0', tk.END)
    for row in formatted_result:
        result_text.insert(tk.END, row + '\n')
    result_text.config(state='disabled')
# 函数用于获取文件夹下的文件列表
def get_file_list(folder_path):
    file_list = []
    for filename in os.listdir(folder_path):
        file_list.append(filename)
    return file_list
# 点击单击事件处理函数
def handle_click(event):
    global path 
    index = result_text.index(tk.CURRENT)
    start_index = index.split('.')[0] + '.0'
    end_index = index.split('.')[0] + '.end'
    folder_path = result_text.get(start_index, end_index).strip()  # 删除行首和行末的空白字符
    if folder_path.endswith('.md'):
        folder_path = path + "\\" + folder_path
        convert_md_to_html(folder_path)
        return
    elif folder_path:
        path = folder_path
        file_list = get_file_list(folder_path)
        
        result_text.config(state='normal')
        result_text.delete('1.0', tk.END)
        
        if len(file_list) > 0:
            for filename in file_list:
                result_text.insert(tk.END, filename + '\n')
        else:
            result_text.insert(tk.END, '文件夹为空')
        
        result_text.config(state='disabled')
# md转为HTML并打开
def convert_md_to_html(filepath):
    # 读取Markdown文件内容
    with open(filepath, 'r', encoding='utf-8') as f:
        markdown_text = f.read()

    

    # 转换Markdown为HTML
    html_content = markdown.markdown(markdown_text, extensions=['extra'])
    # 自定义css样式与LaTeX翻译
    html_template = f'''
    <style>
        pre {{
            background-color: #f4f4f4;
            margin: 10px;
            padding: 10px
        }}
    </style>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <script>
        MathJax = {{
            tex: {{inlineMath: [['$', '$'], ['\\\\(', '\\\\)']]}}
        }}
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    '''
    with open("output.html", 'w', encoding='utf-8') as f:
        f.write(html_template)

    webbrowser.open("output.html")
# 清空数据库
def clear_database():
    # 数据库连接
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 清空数据表
    cursor.execute("DELETE FROM problem_table")
    conn.commit()

    # 关闭数据库连接
    conn.close()

    # 清空查询结果显示区域
    result_text.config(state='normal')
    result_text.delete('1.0', tk.END)
    result_text.config(state='disabled')
def close_window():
    window.destroy()  # 销毁窗口

# 创建GUI界面
window = tk.Tk()
window.title("题目爬取工具")
window.geometry("800x600")
# 开始号数
start_label = tk.Label(window, text="开始号数")
start_label.place(x = 160,y = 30)
start_entry = tk.Entry(window)
start_entry.place(x = 110,y = 60)
# 终止号数
end_label = tk.Label(window, text="终止号数")
end_label.place(x = 360,y = 30)
end_entry = tk.Entry(window)
end_entry.place(x = 310,y = 60)
# 总题数
total_label = tk.Label(window, text="总题数")
total_label.place(x = 560,y = 30)
total_entry = tk.Entry(window)
total_entry.place(x = 510,y = 60)
# 开始按钮
start_button = tk.Button(window, text="开始爬取", command=main)
start_button.place(x = 360,y = 500)
# 设置关闭窗口时调
window.protocol("WM_DELETE_WINDOW", close_window)
# 难度选择下拉框
difficulty_var = tk.StringVar()
ttk.Label(window, text='难度：').place(x = 120,y = 100)
difficulty_combobox = ttk.Combobox(window, textvariable=difficulty_var,
                                    values=["暂未评定", "入门", "普及−", "普及/提高−", "普及+/提高","提高+/省选", "省选/NOI−","NOI/NOI+/CTSC"])
difficulty_combobox.place(x = 160,y = 100)

# 标签输入框
tags_var = tk.StringVar()
ttk.Label(window, text='标签：').place(x = 120,y = 130)
tags_entry = ttk.Entry(window, width=20, textvariable=tags_var)
tags_entry.place(x = 170,y = 130)

# 题号输入框
problem_id_var = tk.StringVar()
ttk.Label(window, text='题号：').place(x = 120,y = 160)
problem_id_entry = ttk.Entry(window, width=20, textvariable=problem_id_var)
problem_id_entry.place(x = 170,y = 160)

# 题目名称输入框
problem_title_var = tk.StringVar()
ttk.Label(window, text='题目名称：').place(x = 100,y = 200)
problem_title_entry = ttk.Entry(window, width=20, textvariable=problem_title_var)
problem_title_entry.place(x = 170,y = 200)
# 查询按钮
ttk.Button(window, text='查询', command=query).place(x = 180,y = 230)

# 查询结果显示区域
result_text = tk.Text(window, wrap=tk.WORD, state='disabled',width=50,height=20)
result_text.place(x = 350,y = 150)
# 绑定点击单击事件
result_text.bind('<Button-1>', handle_click)
# 清空数据表
ttk.Button(window, text='清空数据库', command=clear_database).place(x=170, y=300)
window.mainloop()
