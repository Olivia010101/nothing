import argparse
import base64
import re
import sys

import requests
import yaml

sys.path.append(".")

from autoPush import pushRepo
from createConfigYaml import *
from processProxy import *

protocol_regex = re.compile(
    r"^(?:http|https|socks4|socks5|ss|vmess|trojan|ssr|vless|ws)://"
)


def downloadFile(index, url, httpProxy):
    print("开始下载{}：{}".format(index, url), end=" ", flush=True)
    file = None
    try:
        downloadProxy = None
        if httpProxy is not None:
            downloadProxy = {"http": httpProxy, "https": httpProxy}

        req = requests.get(url, proxies=downloadProxy)
        if req.status_code == 200:
            print("下载成功", end="\n", flush=True)
            file = req.text.replace("!<str> ", "")
        else:
            print("下载失败")
    except requests.exceptions.SSLError:
        print("SSLError 下载失败")
    except requests.exceptions.MissingSchema:
        print("Invalid URL: url")
    except requests.exceptions.ConnectionError:
        print("Connection aborted")
    # protocol_pattern = r"^(?:http|https|socks4|socks5|ss|vmess|trojan|ssr|vless|ws)://"
    if file is not None and protocol_regex.match(file) is not None:
        file = base64.b64encode(file)

    return file


def parserSourceUrl(sourceFile):
    # logging.info("开始解析有效的URL")
    allUrls = set()  # 使用集合去重
    valid_urls = []

    try:
        for url in sourceFile:
            stripped_url = url.strip()
            if stripped_url.startswith("#"):  # 删除注释
                continue
            if not stripped_url:  # 删除空行
                continue
            if not stripped_url.startswith("//"):  # 确保不是注释行
                if stripped_url not in allUrls:
                    allUrls.add(stripped_url)
                    valid_urls.append(stripped_url)
                    # logging.info(stripped_url)

        # logging.info(f"解析完成，共获得 {len(valid_urls)} 个有效URL")
        print(f"解析完成，共获得 {len(valid_urls)} 个有效URL")
        return valid_urls

    except Exception as e:
        # logging.error(f"解析过程中出现错误: {e}")
        print(e)
        return []


# 配置日志记录
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )


def getProxyFromSource(sourcePath, httpProxy):
    proxyPool = []

    # 验证文件路径合法性
    if not sourcePath or not sourcePath.strip():
        # 3 logging.error("无效的文件路径")
        print("无效的文件路径")
        return []

    try:
        with open(sourcePath, encoding="utf8") as file:
            sources = parserSourceUrl(file.read().strip().splitlines())
    except FileNotFoundError:
        # logging.error(f"文件 {sourcePath} 未找到")
        print(f"文件 {sourcePath} 未找到")
        return []
    except Exception as e:
        # logging.error(f"读取文件失败: {e}")
        print(e)
        return []

    for index, url in enumerate(sources):
        sub_url = url
        if url.endswith(".md"):
            continue
        try:
            download = downloadFile(index + 1, url, httpProxy)
            file = yaml.safe_load(download)
            if (
                file
                and "proxies" in file
                and isinstance(file["proxies"], list)
                and file["proxies"]
            ):
                proxyPool.extend(file["proxies"])
                # logging.info("成功获得节点")
                print("成功获得节点")
            else:
                print(f"下载失败，请检查{url}是否有效")
        except yaml.YAMLError as e:
            # config_url = "https://fastly.jsdelivr.net/gh/ACL4SSR/ACL4SSR/blob@master/Clash/config/ACL4SSR.ini"
            # options = "emoji=true&list=true&xudp=false&udp=true&tfo=false&expand=true&scv=true&fdn=true&new_name=true"
            options = (
                "emoji=true&list=true&udp=true&tfo=false&scv=false&fdn=true&sort=true"
            )

            # url = f"https://url.v1.mk/sub?target=clash&url={sub_url}&insert=false&config={config_url}&{options}"
            url = f"https://api.dler.io/sub?target=clash&url={sub_url}&{options}"

            try:
                download = downloadFile(index + 1, url, httpProxy)
                file = yaml.safe_load(download)
                if (
                    file
                    and "proxies" in file
                    and isinstance(file["proxies"], list)
                    and file["proxies"]
                ):
                    proxyPool.extend(file["proxies"])
                    print("成功获得节点")
                else:
                    print(f"下载失败，请检查{url}是否有效")
            except yaml.YAMLError as e:
                # logging.error(f"解析节点失败。 Error：{e}")
                print(f"解析节点失败。 Error：{e}")

    print(f"原始获取节点数量: {len(proxyPool)}")
    proxies = removeNodes(proxyPool)
    print(f"删除不符合节点后，节点数量: {len(proxies)}")

    return proxies


parser = argparse.ArgumentParser()
parser.add_argument(
    "--urlfile", type=str, default="source.url", help="指定下载clash订阅链接的文件"
)
parser.add_argument(
    "--config", type=str, default="default.config", help="生成clash配置文件的模板文件"
)
parser.add_argument(
    "--file", type=str, default="list.yaml", help="最终生成的clash配置文件"
)
parser.add_argument("--http", default=None, help="指定http proxy")
# parser.add_argument(
#     "--https", type=str, default="http://127.0.0.1:7789", help="指定https proxy"
# )
parser.add_argument("--host", type=str, default="127.0.0.1", help="指定clash host")
parser.add_argument("--port", type=int, default=7790, help="指定clash web ui的prot")
parser.add_argument(
    "--auth",
    type=str,
    default="mihomo-password",
    help="指定clash web ui的Authorization",
)
parser.add_argument(
    "--min",
    type=int,
    default=1,
    help="生成clash配置文件所需要的最少节点数量.默认数值为10",
)
parser.add_argument(
    "--max",
    type=int,
    default=500,
    help="延迟测试中通过测试的最大节点数量。超过这个数字后，将停止延迟测试。默认数值为50",
)
parser.add_argument("--timeout", type=int, default=3000, help="延迟测试运行的时间")
parser.add_argument(
    "--testurl",
    type=str,
    default="http://cp.cloudflare.com/generate_204",
    help="指定延迟测试使用的url",
)
# parser.add_argument("--testurl", type=str, default="https://www.youtube.com/generate_204", help="指定延迟测试使用的url")
parser.add_argument(
    "--nopush", action="store_true", help="不将生成的clash配置文件上传至github"
)
parser.add_argument(
    "--retry", type=int, default=5, help="推送至github失败后重试的次数。默认数值为5次"
)

createClash = parser.add_mutually_exclusive_group(required=True)
createClash.add_argument(
    "--local",
    action="store_true",
    help="对--file指定文件进行处理后，生成延迟测试所需要的clash配置文件",
)
createClash.add_argument(
    "--download",
    action="store_true",
    help="下载公开的订阅文件，在本地生成--file指定的延迟测试所需要的clash配置文件。",
)
createClash.add_argument(
    "--delay",
    action="store_true",
    help="对指定的配置文件进行延迟测试，生成--file指定的配置文件。默认成功后会推送至github",
)
createClash.add_argument(
    "--location",
    action="store_true",
    help="对--file指定文件节点按照地区分类后生成配置文件。默认成功后会推送至github",
)
createClash.add_argument("--onlypush", action="store_true", help="只推送提交至github")

args = parser.parse_args()


print(f"自动生成配置文件所需的最小节点数量为：{args.min}")
if args.local:  # 处理指定的clash配置文件，删除里面不符合要求的节点，生成新的配置文件
    print(f"开始处理文件{args.file}，删除其中不符合要求的节点。")
    proxies = yaml.load(
        open(args.file, encoding="utf8").read(), Loader=yaml.FullLoader
    )["proxies"]
    proxies = removeNodes(proxies)
    if len(proxies) > args.min:
        creatTestConfig(proxies, args.config, args.file)
    else:
        print("有效节点数量不足，不生成clash配置文件")
elif (
    args.download
):  # 根据urlfile文件中的订阅链接下载配置文件，删除里面不符合要求的节点，生成新的配置文件
    proxies = getProxyFromSource(args.urlfile, args.http)
    if len(proxies) > args.min:
        creatTestConfig(proxies, args.config, args.file)
    else:
        print("有效节点数量不足，不生成clash配置文件")
    if not args.nopush:
        # pushFile(args.file, args.retry)
        pushRepo(args.retry)
    else:
        print("指定不推送至github")

elif args.delay:  # 对配置文件中的节点进行延迟测试，删除延迟不符合要求的节点。
    print(f"延迟测试通过的最大节点数量：{args.max}")
    # proxies = teseAllProxy(
    #     args.file, args.max, args.host, args.port, args.auth, args.timeout, args.testurl
    # )
    proxies = asyncio.run(
        testAllProxy(
            args.file,
            args.max,
            args.host,
            args.port,
            args.auth,
            args.timeout,
            args.testurl,
        )
    )
    # output_file = str(args.file).replace(".yaml", "_delay.yaml")
    if len(proxies) > args.min:
        creatConfig(
            proxies,
            args.config,
            args.file,
            args.http,
            # args.https,
        )
    else:
        print("有效节点数量不足，不生成clash配置文件")
    if not args.nopush:
        # pushFile(output_file, args.retry)
        pushRepo(args.retry)
    else:
        print("指定不推送至github")
elif args.location:
    print("开始按照地区对节点进行分类。")
    proxies = yaml.load(
        open(args.file, encoding="utf8").read(), Loader=yaml.FullLoader
    )["proxies"]
    creatConfig(
        proxies,
        args.config,
        str(args.file).replace(".yaml", "_loc.yaml"),
        args.http,
        # args.https,
    )
    if not args.nopush:
        # pushFile(args.file, args.retry)
        pushRepo(args.retry)
    else:
        print("指定不推送至github")
# elif(args.onlypush):
#     pushRepo(args.retry)
else:
    print("invalid parma")
