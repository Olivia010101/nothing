import requests
import yaml
from lxml import etree

# 目标网页URL
url = "https://www.85la.com/internet-access/free-network-nodes"

# 发送HTTP请求获取网页内容
response = requests.get(url)
print(response)
html_content = response.text

# 使用lxml解析HTML
html = etree.HTML(html_content)

target_xpath = '//*[@id="paging-aa"]/div[1]/div[2]/h2/a'  # 示例XPath路径

# 获取目标元素的值
node_lists = html.xpath(target_xpath)
print(len(node_lists))
if len(node_lists) < 1:
    print("no url")
    exit(0)
new_url = node_lists[0].attrib["href"]  # 获取属性值

print(new_url)


response = requests.get(new_url)
html_content = response.text
html = etree.HTML(html_content)
target_xpath = '//*[@id="md_content_2"]/div/div[5]/div[3]/p/a'
subscript_url = html.xpath(target_xpath)[0].text.strip()


response = requests.get(subscript_url)
response.raise_for_status()
yaml_content = yaml.safe_load(response.text)

proxies = yaml_content["proxies"]

if proxies is not None:
    # 创建一个新的YAML结构
    new_yaml_content = {"proxies": proxies}

    # 将新的YAML结构写入到文件
    with open("clash/85la.yaml", "w", encoding="utf-8") as file:
        yaml.dump(new_yaml_content, file, allow_unicode=True)
    print("字段已成功写入到 85la.yaml 文件中")
else:
    print("未找到目标字段，无法写入文件")

