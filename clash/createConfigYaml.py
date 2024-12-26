import re
import socket

import requests
import yaml

ipv4_regex = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")


def is_valid_ip(ip):
    return ipv4_regex.match(ip) is not None


def getPorxyCountry(index, proxy, httpProxy, Authorization="mihomo-password"):
    country = "未知地区"
    try:
        proxies = {
            "http": httpProxy,
            "https": httpProxy,
        }

        ip = socket.gethostbyname(proxy["server"])
        if not is_valid_ip(ip):
            dns_url = "http://127.0.0.1:17790/dns/query"
            hostname = proxy["server"]
            # headers = {"accept": "application/dns-json"}
            header = {"Authorization": f"Bearer {Authorization}"}
            req = requests.get(url=f"{dns_url}?name={hostname}&type=A", headers=header)

            ip = req.json()["Answer"][0]["data"]

        data = requests.get(f"http://ip.plyz.net/ip.ashx?ip={ip}", proxies=proxies).text
        if len(data) != 0:
            country = data.split("|")[1].split()[0]
    except Exception as e:
        print(e)

    print(f"节点{index}: {proxy['server']} {country}")
    return country


def createGroup(name, groupType, proxies):
    allType = ["select", "load-balance", "url-test", "fallback"]
    assert groupType in allType

    group = {
        "name": name,
        "type": groupType,
        "proxies": proxies,
    }

    if groupType != "select":
        group["url"] = "https://twitter.com/favicon.ico"
        group["interval"] = 300

    return group


def createLocationProxyGroup(proxies, httpProxy="http://127.0.0.1:7789"):
    print("按照ip地址查询节点所属地区")

    location = dict()
    for index, proxy in enumerate(proxies):
        country = getPorxyCountry(index + 1, proxy, httpProxy)
        # if country in ["未知地区", "中国"]:
        if "中国" in country or "未知" in country:
            continue
        countryGroup = (
            location[country]
            if (country in location)
            else createGroup(country, "url-test", [])
        )
        proxy["name"] = f"{country}-{len(countryGroup['proxies']) + 1}"
        countryGroup["proxies"].append(proxy["name"])

        location[country] = countryGroup

    return location


def creatConfig(proxies, defaultFile, configFile, httpProxy):
    defaultConfig = open(defaultFile, encoding="utf8").read()
    config = yaml.load(defaultConfig, Loader=yaml.FullLoader)

    countryGroup = createLocationProxyGroup(proxies, httpProxy)

    proxiesNames = [proxy["name"] for proxy in proxies]

    config["proxies"] = (
        proxies if config["proxies"] == None else config["proxies"] + proxies
    )

    config["proxy-groups"] = []
    config["proxy-groups"].append(
        createGroup(
            "proxinode",
            "select",
            ["选择地区", "延迟最低", "故障转移", "负载均衡", "手动选择"],
            # ["选择地区"],
        )
    )

    selectCountry = createGroup("选择地区", "select", [])

    allCountry = []
    for country in countryGroup:
        if country != "内网IP":
            selectCountry["proxies"].append(country)
            allCountry.append(countryGroup[country])

    config["proxy-groups"].append(selectCountry)
    config["proxy-groups"].append(createGroup("延迟最低", "url-test", proxiesNames))
    config["proxy-groups"].append(createGroup("故障转移", "fallback", proxiesNames))
    config["proxy-groups"].append(createGroup("负载均衡", "load-balance", proxiesNames))
    config["proxy-groups"].append(createGroup("手动选择", "select", proxiesNames))

    config["proxy-groups"] += allCountry

    with open(configFile, "w", encoding="utf-8") as file:
        yaml.dump(config, file, encoding="utf-8", allow_unicode=True)

    print("生成clash配置文件：{}".format(configFile))


def creatTestConfig(proxies, defaultFile, testFile):
    defaultConfig = open(defaultFile, encoding="utf8").read()
    config = yaml.load(defaultConfig, Loader=yaml.FullLoader)

    proxiesNames = [proxy["name"] for proxy in proxies]

    config["proxies"] = (
        proxies if config["proxies"] == None else config["proxies"] + proxies
    )

    config["proxy-groups"] = [createGroup("proxinode", "url-test", proxiesNames)]

    with open(testFile, "w", encoding="utf-8") as file:
        yaml.dump(config, file, encoding="utf-8", allow_unicode=True)

    print("生成clash配置文件：{}".format(testFile))


if __name__ == "__main__":
    profileFile = "list.yaml"
    with open(profileFile, encoding="utf8") as fp:
        listFile = yaml.load(fp.read(), Loader=yaml.FullLoader)
        createLocationProxyGroup(listFile["proxies"])
