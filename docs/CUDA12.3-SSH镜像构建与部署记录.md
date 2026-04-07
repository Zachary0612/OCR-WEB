# CUDA 12.3 + SSH Docker 镜像构建记录

## 镜像信息

- 基础镜像：`nvidia/cuda:12.3.2-devel-ubuntu22.04`
- 镜像名称：`cuda12.3-ssh:latest`
- 内容：CUDA 12.3 完整开发工具链 + SSH 服务
- 导出文件：`cuda12.3-ssh.tar`（3.68 GB）
- SSH 账号：`root` / `root123`

## 构建步骤

### 1. 编写 Dockerfile

```dockerfile
FROM nvidia/cuda:12.3.2-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=Asia/Shanghai

RUN apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing \
       openssh-server curl wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd \
    && echo 'root:root123' | chpasswd \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
```

### 2. 拉取基础镜像

```bash
docker pull docker.m.daocloud.io/nvidia/cuda:12.3.2-devel-ubuntu22.04
```

### 3. 构建镜像

```bash
docker build --no-cache -t cuda12.3-ssh:latest .
```

### 4. 导出 tar 文件

```bash
docker save cuda12.3-ssh:latest -o cuda12.3-ssh.tar
```

## 部署步骤（服务器端）

### 1. 上传 tar 文件到服务器

用 FTP 工具将 `cuda12.3-ssh.tar` 上传到服务器，如 `/data/`

### 2. 加载镜像

```bash
docker load -i /data/cuda12.3-ssh.tar
```

### 3. 启动容器

```bash
docker run -d --name cuda-server --gpus all --shm-size 8g -p 2222:22 -p 8000:8000 cuda12.3-ssh:latest
```

### 4. SSH 连接

```bash
ssh root@服务器IP -p 2222
# 密码: root123
```

### 5. 验证

```bash
nvcc --version
nvidia-smi
```
