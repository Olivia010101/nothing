from datetime import datetime

import git


def pushRepo(retry):  # 将提交推送至github
    repo = git.Repo(".")
    listStatus = repo.git.status(".")
    # repo.alternates
    print(listStatus)
    addMessage = repo.git.add(["./proxypool"])
    print(addMessage)
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    commitMessage = repo.index.commit(f"[update] {formatted_time}")
    print(commitMessage)
    for i in range(retry):
        print(f"开始第{i + 1}次推送：", end="", flush=True)
        message = repo.remotes.origin.push("master")
        # print(message)
        if not message.error:
            print("推送成功。")
            break

        if i == (retry - 1):
            print("达到最大重试次数，退出推送。")


def pushFile(file, retry):  # 检查文件是否有修改，如果有修改，则将修改推送至github
    repo = git.Repo(".")

    listStatus = repo.git.status(file)
    # print(listStatus)
    if "modified" in listStatus or "Untracked" in listStatus:
        print(f"{file}已更新，开始推送至github。")
        pushRepo(retry)
    else:
        print(f"{file}未更新，无需推送至github。")


if __name__ == "__main__":
    pushRepo(1)
