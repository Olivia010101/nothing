import asyncio
import logging

import aiohttp
import yaml


def removeDuplicateNode(proxyPool):  # 删除重复节点
    # checkLists = ["name", "server"]
    # checkLists = ["server"]

    # allProxy = proxyPool
    serverList = []
    nameList = []
    serverProxies = []
    allProxies = []

    # filt the server
    for proxy in proxyPool:
        if proxy["server"] in serverList:
            continue
        serverProxies.append(proxy)
        serverList.append(proxy["server"])
    cnt = 0
    for proxy in serverProxies:
        if proxy["name"] in nameList:
            proxy["name"] = proxy["name"] + "_" + str(cnt)
            cnt += 1
        allProxies.append(proxy)
        nameList.append(proxy["name"])
    # allProxy = proxies
    # for item in checkLists:
    #     proxiesItem = []
    #     proxies = []
    #     for proxy in allProxy:
    #         if proxy[item] in proxiesItem:
    #             continue
    #         proxies.append(proxy)
    #         proxiesItem.append(proxy[item])
    # allProxy = proxies

    print(f"after removeDuplicateNode, 剩余节点数量{len(allProxies)}")
    return allProxies


def removeNotSupportCipher(
    proxyPool, ignoreIssueCipher=False
):  # 删除cipher不符合条件的节点
    notSupportCipher = ["ss", "chacha20-poly1305"]
    notSupportCipherWithType = {
        "ssr": ["none", "rc4", "rc4-md5"],
        "ss": ["aes-128-cfb", "aes-256-cfb", "rc4-md5"],
        # "vmess": ["none", "h2", "auto", "grpc"],
        "vmess": ["none", "h2", "grpc"],
    }
    proxies = []
    for proxy in proxyPool:
        if "cipher" in proxy and proxy["cipher"] in notSupportCipher:
            continue
        if (
            not ignoreIssueCipher
            and proxy["type"] in notSupportCipherWithType.keys()
            and proxy["cipher"] in notSupportCipherWithType[proxy["type"]]
        ):
            continue
        proxies.append(proxy)

    print(f"after removeNotSupportCipher, 剩余节点数量{len(proxies)}")
    return proxies


def removeNotSupportUUID(proxyPool):  # 删除uuid不符合条件的节点
    notSupportUUID = ["Free", ""]
    proxies = []
    for proxy in proxyPool:
        if "uuid" in proxy and proxy["uuid"] in notSupportUUID:
            continue
        proxies.append(proxy)

    print(f"after removeNotSupportUUID, 剩余节点数量{len(proxies)}")
    return proxies


def removeNotSupportType(proxyPool):  # 删除type不符合条件的节点
    # notSupportType = ["vless", "hysteria", "hysteria2"]
    notSupportType = ["socks5", "http", "ssh"]
    proxies = []
    for proxy in proxyPool:
        if "type" in proxy and proxy["type"] in notSupportType:
            continue
        if "reality-opts" in proxy or (
            "flow" in proxy and "xtls-rprx-vision" in proxy["flow"]
        ):
            continue
        proxies.append(proxy)

    print(f"after removeNotSupportType, 剩余节点数量{len(proxies)}")

    return proxies


# def removeSpeedtestIssues(proxies):
# not_supprt_cipher_with_type = {}


def removeNodes(proxyPool):
    proxies = removeDuplicateNode(proxyPool)
    proxies = removeNotSupportCipher(proxies)
    # proxies = removeNotSupportUUID(proxies)
    proxies = removeNotSupportType(proxies)

    return proxies


async def getProxyDelay(
    index, proxyName, host, port, Authorization, timeout, testurl, session
):
    bPassTest = False
    url = f"http://{host}:{port}/proxies/{proxyName}/delay?url={testurl}&timeout={timeout}"
    headers = {
        "Authorization": f"Bearer {Authorization}",
    }

    try:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logging.error(f"请求失败: {url}, 状态码: {response.status}")
                return bPassTest

            delay = await response.json()
            if "delay" in delay:
                delay = delay["delay"]
                bPassTest = True
            elif "message" in delay:
                delay = delay["message"]
            else:
                logging.error(f"未知响应格式: {delay}")
                return bPassTest

            logging.info(f"节点{index}: {proxyName}: {delay}")

    except Exception as e:
        logging.error(f"请求异常: {e}")
        return bPassTest

    return bPassTest


# def getProxyDelay(index, proxyName, host, port, Authorization, timeout, testurl):
#     bPassTest = False

#     url = f"http://{host}:{port}/proxies/{proxyName}/delay?url={testurl}&timeout={timeout}"
#     header = {
#         "Authorization": f"Bearer {Authorization}",
#     }

#     # param = {"timeout": timeout, "url": testurl}
#     # status_code = requests.get(url, headers=header, params=param).status_code
#     # if status_code != 200:
#     #     print(url)
#     #     return bPassTest
#     try:
#         # delay = eval(requests.get(url, headers=header, params=param).text)
#         delay = eval(requests.get(url, headers=header).text)
#     except Exception as e:
#         print(e)
#         # print(requests.get(url, headers=header, params=param).status_code)
#         # print(url)
#         return bPassTest

#     if "delay" in delay:
#         delay = delay["delay"]
#         bPassTest = True
#     elif "message" in delay:
#         delay = delay["message"]
#     else:
#         assert 0

#     print(f"节点{index}: {proxyName}: {delay}")

#     return bPassTest


# def teseAllProxy(
#     configFile,
#     maxProxy,
#     host="127.0.0.1",
#     port=9097,
#     Authorization="clash-password",
#     timeout=3000,
#     testurl="https://www.youtube.com/generate_204",
# ):
#     passProxy = []
#     with open(configFile, encoding="utf8") as fp:
#         listFile = yaml.load(fp.read(), Loader=yaml.FullLoader)
#         allProxy = listFile["proxies"]
#         print(f"延迟测试超时时间为：{timeout}")
#         print(f"延迟测试url为：{testurl}")
#         print(f"测试节点总数为：{len(allProxy)}")
#         # random.shuffle(allProxy)
#         try:
#             for index, proxy in enumerate(allProxy):
#                 if getProxyDelay(
#                     index + 1,
#                     proxy["name"],
#                     host,
#                     port,
#                     Authorization,
#                     timeout,
#                     testurl,
#                 ):
#                     passProxy.append(proxy)
#                 #     print(f"节点 {proxy['name']} 测速正常")
#                 # else:
#                 #     print(f"节点 {proxy['name']} 测速异常")

#                 if ((index + 1) % 30) == 0:
#                     print(f"测试正常节点: {len(passProxy)}/{index + 1}")

#                 if len(passProxy) == maxProxy:  # 获得有效的的节点数已经足够多 退出测试
#                     print("获得预期最大节点数量，退出延迟测试。")
#                     break
#         except KeyboardInterrupt:
#             print("取消测试，延迟测试结束。")
#         except Exception as e:
#             print(f"发生错误：{e}。延迟测试结束。")

#         print(f"测试正常节点: {len(passProxy)}/{len(allProxy)}")


#     return passProxy
async def testAllProxy(
    configFile,
    maxProxy,
    host="127.0.0.1",
    port=9097,
    Authorization="clash-password",
    timeout=3000,
    testurl="https://www.youtube.com/generate_204",
):
    passProxy = []
    with open(configFile, encoding="utf8") as fp:
        listFile = yaml.load(fp.read(), Loader=yaml.FullLoader)
        allProxy = listFile["proxies"]
        print(f"延迟测试超时时间为：{timeout}")
        print(f"延迟测试url为：{testurl}")
        print(f"测试节点总数为：{len(allProxy)}")

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, proxy in enumerate(allProxy):
            task = asyncio.create_task(
                getProxyDelay(
                    index + 1,
                    proxy["name"],
                    host,
                    port,
                    Authorization,
                    timeout,
                    testurl,
                    session,
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        for index, result in enumerate(results):
            if result:
                passProxy.append(allProxy[index])
                if ((index + 1) % 30) == 0:
                    print(f"测试正常节点: {len(passProxy)}/{index + 1}")

                if len(passProxy) == maxProxy:
                    print("获得预期最大节点数量，退出延迟测试。")
                    break

    print(f"测试正常节点: {len(passProxy)}/{len(allProxy)}")
    return passProxy


if __name__ == "__main__":
    maxProxy = 5000
    passProxies = asyncio.run(testAllProxy("tmp_list.yaml", maxProxy))
    print(passProxies)
