# NVIDIA H20 GPU 鏈嶅姟鍣ㄩ儴缃叉墜鍐?
> **閫傜敤鍦烘櫙**锛氬湪鎼浇 NVIDIA H20 GPU 鐨?Linux 鏈嶅姟鍣ㄤ笂浠庨浂閮ㄧ讲 OCR 妗ｆ璇嗗埆绯荤粺  
> **棰勮鑰楁椂**锛?-3 灏忔椂锛堝惈妯″瀷棣栨涓嬭浇锛? 
> **鏈€鍚庢洿鏂?*锛?026-03-30

---

## 鐩綍

1. [绯荤粺瑕佹眰](#1-绯荤粺瑕佹眰)
2. [鏈嶅姟鍣ㄧ幆澧冨噯澶嘳(#2-鏈嶅姟鍣ㄧ幆澧冨噯澶?
3. [NVIDIA 椹卞姩涓?CUDA 瀹夎](#3-nvidia-椹卞姩涓?cuda-瀹夎)
4. [cuDNN 瀹夎](#4-cudnn-瀹夎)
5. [PostgreSQL 鏁版嵁搴撳畨瑁匽(#5-postgresql-鏁版嵁搴撳畨瑁?
6. [Redis 缂撳瓨瀹夎](#6-redis-缂撳瓨瀹夎)
7. [Python 鐜閰嶇疆](#7-python-鐜閰嶇疆)
8. [椤圭洰浠ｇ爜閮ㄧ讲](#8-椤圭洰浠ｇ爜閮ㄧ讲)
9. [鍚庣鏈嶅姟閰嶇疆](#9-鍚庣鏈嶅姟閰嶇疆)
10. [鍓嶇鏋勫缓涓庨儴缃瞉(#10-鍓嶇鏋勫缓涓庨儴缃?
11. [Nginx 鍙嶅悜浠ｇ悊閰嶇疆](#11-nginx-鍙嶅悜浠ｇ悊閰嶇疆)
12. [SSL 璇佷功閰嶇疆锛堝彲閫夛級](#12-ssl-璇佷功閰嶇疆鍙€?
13. [鍒濆鏁版嵁瀵煎叆](#13-鍒濆鏁版嵁瀵煎叆)
14. [鏈嶅姟楠岃瘉](#14-鏈嶅姟楠岃瘉)
15. [systemd 鏈嶅姟绠＄悊](#15-systemd-鏈嶅姟绠＄悊)
16. [鏃ュ織绠＄悊](#16-鏃ュ織绠＄悊)
17. [澶囦唤涓庢仮澶峕(#17-澶囦唤涓庢仮澶?
18. [鎬ц兘浼樺寲](#18-鎬ц兘浼樺寲)
19. [甯歌闂鎺掓煡](#19-甯歌闂鎺掓煡)
20. [杩愮淮鍛戒护閫熸煡](#20-杩愮淮鍛戒护閫熸煡)

---

## 1. 绯荤粺瑕佹眰

### 1.1 纭欢瑕佹眰

| 缁勪欢 | 鏈€浣庨厤缃?| 鎺ㄨ崘閰嶇疆 |
|------|----------|----------|
| **GPU** | NVIDIA H20 脳 1 | NVIDIA H20 脳 1 |
| **CPU** | 8 鏍?| 16 鏍稿強浠ヤ笂 |
| **鍐呭瓨** | 32 GB | 64 GB 鍙婁互涓?|
| **绯荤粺鐩?* | 100 GB SSD | 200 GB NVMe SSD |
| **鏁版嵁鐩?* | 500 GB | 1 TB 鍙婁互涓?|
| **缃戠粶** | 100 Mbps | 1 Gbps |

### 1.2 杞欢瑕佹眰

| 杞欢 | 鐗堟湰瑕佹眰 |
|------|----------|
| **鎿嶄綔绯荤粺** | Ubuntu 22.04 LTS (鎺ㄨ崘) / Ubuntu 20.04 LTS |
| **NVIDIA 椹卞姩** | 鈮?535.x |
| **CUDA** | 12.x (鎺ㄨ崘 12.2 鎴?12.4) |
| **cuDNN** | 8.9.x |
| **Python** | 3.10.x |
| **PostgreSQL** | 14.x / 15.x |
| **Redis** | 7.x |
| **Node.js** | 18.x LTS / 20.x LTS |
| **Nginx** | 1.18+ |

### 1.3 NVIDIA H20 GPU 鐗规€?
NVIDIA H20 鏄笓涓轰腑鍥藉競鍦鸿璁＄殑鏁版嵁涓績 GPU锛?
- **鏄惧瓨**锛?6 GB HBM3
- **绠楀姏**锛氶€傚悎澶ц妯?AI 鎺ㄧ悊
- **CUDA 鏍稿績**锛氬厖瓒崇殑骞惰璁＄畻鑳藉姏
- **鍔熻€?*锛氱害 400W TDP

> **閲嶈**锛欻20 瀹屽叏鍏煎鏍囧噯 CUDA 宸ュ叿閾撅紝鏈」鐩殑 PaddlePaddle GPU 鐗堟湰鍙洿鎺ヨ繍琛屻€?
### 1.4 绔彛瑙勫垝

| 鏈嶅姟 | 绔彛 | 璇存槑 |
|------|------|------|
| Nginx (HTTP) | 80 | 鍓嶇鍏ュ彛 |
| Nginx (HTTPS) | 443 | HTTPS 鍏ュ彛锛堝彲閫夛級 |
| 鍚庣 API | 8000 | FastAPI 鏈嶅姟 |
| 鍓嶇寮€鍙?| 3000 | 浠呭紑鍙戞椂浣跨敤 |
| PostgreSQL | 5432 | 鏁版嵁搴?|
| Redis | 6379 | 缂撳瓨 |

---

## 2. 鏈嶅姟鍣ㄧ幆澧冨噯澶?
### 2.1 绯荤粺鏇存柊

```bash
# 鏇存柊杞欢鍖呭垪琛?sudo apt update

# 鍗囩骇宸插畨瑁呯殑杞欢鍖?sudo apt upgrade -y

# 瀹夎鍩虹宸ュ叿
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    htop \
    tmux \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
```

### 2.2 鍒涘缓椤圭洰鐢ㄦ埛锛堟帹鑽愶級

```bash
# 鍒涘缓涓撶敤鐢ㄦ埛
sudo useradd -m -s /bin/bash ocruser

# 璁剧疆瀵嗙爜
sudo passwd ocruser

# 娣诲姞鍒?sudo 缁勶紙鍙€夛紝鐢ㄤ簬璋冭瘯锛?sudo usermod -aG sudo ocruser

# 鍒涘缓椤圭洰鐩綍
sudo mkdir -p /opt/ocr
sudo chown ocruser:ocruser /opt/ocr
```

### 2.3 閰嶇疆鏃跺尯

```bash
# 璁剧疆鏃跺尯涓轰腑鍥芥椂鍖?sudo timedatectl set-timezone Asia/Shanghai

# 楠岃瘉
timedatectl
```

### 2.4 閰嶇疆绯荤粺闄愬埗

缂栬緫 `/etc/security/limits.conf`锛屾坊鍔狅細

```bash
sudo tee -a /etc/security/limits.conf << 'EOF'
# OCR 鏈嶅姟浼樺寲
ocruser soft nofile 65535
ocruser hard nofile 65535
ocruser soft nproc 65535
ocruser hard nproc 65535
EOF
```

### 2.5 閰嶇疆 swap锛堝鏋滃唴瀛樹笉瓒筹級

```bash
# 妫€鏌ュ綋鍓?swap
free -h

# 濡傛灉娌℃湁 swap锛屽垱寤?16GB swap 鏂囦欢
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 姘镐箙鐢熸晥
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 3. NVIDIA 椹卞姩涓?CUDA 瀹夎

### 3.1 妫€鏌?GPU 鐘舵€?
```bash
# 鏌ョ湅 GPU 纭欢
lspci | grep -i nvidia

# 棰勬湡杈撳嚭绫讳技锛?# 3b:00.0 3D controller: NVIDIA Corporation Device 2331 (rev a1)
```

### 3.2 绂佺敤 Nouveau 椹卞姩

```bash
# 妫€鏌?nouveau 鏄惁鍔犺浇
lsmod | grep nouveau

# 濡傛灉鏈夎緭鍑猴紝闇€瑕佺鐢?sudo tee /etc/modprobe.d/blacklist-nouveau.conf << 'EOF'
blacklist nouveau
options nouveau modeset=0
EOF

# 鏇存柊 initramfs
sudo update-initramfs -u

# 閲嶅惎鏈嶅姟鍣?sudo reboot
```

### 3.3 瀹夎 NVIDIA 椹卞姩

**鏂规硶涓€锛氫娇鐢?Ubuntu 瀹樻柟椹卞姩锛堟帹鑽愶級**

```bash
# 鏌ョ湅鎺ㄨ崘椹卞姩
ubuntu-drivers devices

# 鑷姩瀹夎鎺ㄨ崘椹卞姩
sudo ubuntu-drivers autoinstall

# 鎴栨墜鍔ㄦ寚瀹氱増鏈紙H20 鎺ㄨ崘 535 鎴栨洿楂橈級
sudo apt install -y nvidia-driver-535
```

**鏂规硶浜岋細浣跨敤 NVIDIA 瀹樻柟 .run 鏂囦欢**

```bash
# 涓嬭浇椹卞姩锛堜粠 NVIDIA 瀹樼綉鑾峰彇鏈€鏂扮増鏈級
wget https://cn.download.nvidia.com/tesla/535.154.05/NVIDIA-Linux-x86_64-535.154.05.run

# 瀹夎渚濊禆
sudo apt install -y linux-headers-$(uname -r)

# 杩愯瀹夎
sudo chmod +x NVIDIA-Linux-x86_64-535.154.05.run
sudo ./NVIDIA-Linux-x86_64-535.154.05.run
```

### 3.4 楠岃瘉椹卞姩瀹夎

```bash
# 閲嶅惎鍚庨獙璇?sudo reboot

# 鏌ョ湅 GPU 淇℃伅
nvidia-smi
```

**棰勬湡杈撳嚭**锛?
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.154.05   Driver Version: 535.154.05   CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA H20          On   | 00000000:3B:00.0 Off |                    0 |
| N/A   32C    P0    72W / 400W |      0MiB / 98304MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

### 3.5 瀹夎 CUDA Toolkit

```bash
# 娣诲姞 NVIDIA CUDA 浠撳簱
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update

# 瀹夎 CUDA 12.2锛堜笌 H20 椹卞姩鍏煎锛?sudo apt install -y cuda-toolkit-12-2

# 鎴栧畨瑁呭畬鏁?CUDA锛堝寘鍚┍鍔紝濡傛灉涓婇潰娌¤椹卞姩锛?# sudo apt install -y cuda-12-2
```

### 3.6 閰嶇疆 CUDA 鐜鍙橀噺

```bash
# 娣诲姞鍒?~/.bashrc
cat >> ~/.bashrc << 'EOF'

# CUDA 鐜鍙橀噺
export CUDA_HOME=/usr/local/cuda-12.2
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
EOF

# 绔嬪嵆鐢熸晥
source ~/.bashrc

# 楠岃瘉
nvcc --version
```

**棰勬湡杈撳嚭**锛?
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Tue_Aug_15_22:02:13_PDT_2023
Cuda compilation tools, release 12.2, V12.2.140
```

---

## 4. cuDNN 瀹夎

### 4.1 涓嬭浇 cuDNN

浠?[NVIDIA cuDNN 涓嬭浇椤甸潰](https://developer.nvidia.com/cudnn) 涓嬭浇瀵瑰簲鐗堟湰锛堥渶瑕?NVIDIA 璐﹀彿锛夈€?
閫夋嫨锛?*cuDNN v8.9.x for CUDA 12.x** 鈫?**Local Installer for Linux x86_64 (Tar)**

### 4.2 瀹夎 cuDNN

```bash
# 瑙ｅ帇锛堝亣璁句笅杞藉埌 ~/Downloads锛?cd ~/Downloads
tar -xvf cudnn-linux-x86_64-8.9.7.29_cuda12-archive.tar.xz

# 澶嶅埗鏂囦欢鍒?CUDA 鐩綍
sudo cp cudnn-linux-x86_64-8.9.7.29_cuda12-archive/include/cudnn*.h /usr/local/cuda-12.2/include/
sudo cp cudnn-linux-x86_64-8.9.7.29_cuda12-archive/lib/libcudnn* /usr/local/cuda-12.2/lib64/

# 璁剧疆鏉冮檺
sudo chmod a+r /usr/local/cuda-12.2/include/cudnn*.h
sudo chmod a+r /usr/local/cuda-12.2/lib64/libcudnn*

# 鏇存柊閾炬帴鍣ㄧ紦瀛?sudo ldconfig
```

### 4.3 楠岃瘉 cuDNN

```bash
# 妫€鏌?cuDNN 鐗堟湰
cat /usr/local/cuda-12.2/include/cudnn_version.h | grep CUDNN_MAJOR -A 2
```

---

## 5. PostgreSQL 鏁版嵁搴撳畨瑁?
### 5.1 瀹夎 PostgreSQL 15

```bash
# 娣诲姞瀹樻柟浠撳簱
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# 瀵煎叆浠撳簱绛惧悕
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# 鏇存柊骞跺畨瑁?sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15
```

### 5.2 鍚姩骞惰缃紑鏈鸿嚜鍚?
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

### 5.3 鍒涘缓鏁版嵁搴撳拰鐢ㄦ埛

```bash
# 鍒囨崲鍒?postgres 鐢ㄦ埛
sudo -u postgres psql

# 鍦?psql 涓墽琛屼互涓嬪懡浠?```

```sql
-- 鍒涘缓鏁版嵁搴撶敤鎴凤紙淇敼瀵嗙爜锛侊級
CREATE USER ocruser WITH PASSWORD 'YourStrongPassword123!';

-- 鍒涘缓鏁版嵁搴?CREATE DATABASE ocr_db OWNER ocruser;

-- 鎺堜簣鏉冮檺
GRANT ALL PRIVILEGES ON DATABASE ocr_db TO ocruser;

-- 鍏佽鍒涘缓鎵╁睍锛堝鏋滈渶瑕侊級
ALTER USER ocruser CREATEDB;

-- 閫€鍑?\q
```

### 5.4 閰嶇疆杩滅▼璁块棶锛堝闇€锛?
缂栬緫 `/etc/postgresql/15/main/postgresql.conf`锛?
```bash
sudo vim /etc/postgresql/15/main/postgresql.conf

# 淇敼鐩戝惉鍦板潃锛堥粯璁ゅ彧鐩戝惉 localhost锛?listen_addresses = 'localhost'  # 濡傞渶杩滅▼璁块棶鏀逛负 '*'
```

缂栬緫 `/etc/postgresql/15/main/pg_hba.conf`锛?
```bash
sudo vim /etc/postgresql/15/main/pg_hba.conf

# 濡傞渶杩滅▼璁块棶锛屾坊鍔狅細
# host    ocr_db    ocruser    0.0.0.0/0    scram-sha-256
```

```bash
# 閲嶅惎 PostgreSQL
sudo systemctl restart postgresql
```

### 5.5 楠岃瘉鏁版嵁搴撹繛鎺?
```bash
# 娴嬭瘯杩炴帴
psql -h localhost -U ocruser -d ocr_db -c "SELECT version();"

# 杈撳叆瀵嗙爜鍚庡簲鏄剧ず PostgreSQL 鐗堟湰淇℃伅
```

---

## 6. Redis 缂撳瓨瀹夎

### 6.1 瀹夎 Redis 7

```bash
# 娣诲姞瀹樻柟浠撳簱
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

# 瀹夎
sudo apt update
sudo apt install -y redis
```

### 6.2 閰嶇疆 Redis

缂栬緫 `/etc/redis/redis.conf`锛?
```bash
sudo vim /etc/redis/redis.conf
```

淇敼浠ヤ笅閰嶇疆锛?
```conf
# 缁戝畾鍦板潃锛堟湰鏈鸿闂級
bind 127.0.0.1 -::1

# 绔彛
port 6379

# 鍚庡彴杩愯
daemonize yes

# 鏈€澶у唴瀛橈紙鏍规嵁鏈嶅姟鍣ㄩ厤缃皟鏁达級
maxmemory 2gb

# 鍐呭瓨娣樻卑绛栫暐
maxmemory-policy allkeys-lru

# 鎸佷箙鍖栭厤缃?appendonly yes
appendfilename "appendonly.aof"

# 鏃ュ織绾у埆
loglevel notice
logfile /var/log/redis/redis-server.log
```

### 6.3 鍚姩 Redis

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server
```

### 6.4 楠岃瘉 Redis

```bash
redis-cli ping
# 搴旇繑鍥? PONG

redis-cli info server | head -5
```

---

## 7. Python 鐜閰嶇疆

### 7.1 瀹夎 Python 3.10

```bash
# Ubuntu 22.04 鑷甫 Python 3.10
python3 --version

# 濡傛灉鐗堟湰涓嶅鎴栨病鏈夛紝瀹夎
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# 瀹夎 pip
sudo apt install -y python3-pip
```

### 7.2 鍒涘缓铏氭嫙鐜

```bash
# 鍒囨崲鍒伴」鐩洰褰?cd /opt/ocr

# 鍒涘缓铏氭嫙鐜
python3.10 -m venv .venv

# 婵€娲昏櫄鎷熺幆澧?source .venv/bin/activate

# 鍗囩骇 pip
pip install --upgrade pip setuptools wheel
```

### 7.3 閰嶇疆 pip 闀滃儚锛堝姞閫熶笅杞斤級

```bash
# 鍒涘缓 pip 閰嶇疆
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
EOF
```

---

## 8. 椤圭洰浠ｇ爜閮ㄧ讲

### 8.1 鍏嬮殕浠ｇ爜

```bash
# 纭繚鍦ㄩ」鐩洰褰?cd /opt/ocr

# 浠?GitHub 鍏嬮殕锛堟浛鎹负浣犵殑浠撳簱鍦板潃锛?git clone https://github.com/YOUR_USERNAME/OCR.git .

# 鎴栬€呭鏋滅洰褰曢潪绌猴紝鍏堟竻鐞?# rm -rf /opt/ocr/*
# git clone https://github.com/YOUR_USERNAME/OCR.git .
```

### 8.2 鍒涘缓蹇呰鐩綍

```bash
cd /opt/ocr

# 鍒涘缓涓婁紶鐩綍
mkdir -p uploads

# 鍒涘缓缂撳瓨鐩綍
mkdir -p .cache

# 鍒涘缓鏃ュ織鐩綍
mkdir -p logs

# 璁剧疆鏉冮檺
chmod 755 uploads .cache logs
```

### 8.3 瀹夎 Python 渚濊禆

```bash
# 纭繚铏氭嫙鐜宸叉縺娲?source /opt/ocr/.venv/bin/activate

# 瀹夎渚濊禆
pip install -r requirements.txt
```

> **娉ㄦ剰**锛歚paddlepaddle-gpu` 浼氳嚜鍔ㄤ笅杞界害 2-3 GB锛岄娆″畨瑁呴渶瑕佽緝闀挎椂闂淬€?
### 8.4 楠岃瘉 PaddlePaddle GPU

```bash
# 娴嬭瘯 PaddlePaddle GPU
python -c "import paddle; paddle.utils.run_check()"
```

**棰勬湡杈撳嚭**锛?
```
Running verify PaddlePaddle program ...
W0330 14:00:00.000000 12345 gpu_resources.cc:119] Please NOTE: device: 0, GPU Compute Capability: 9.0, Driver API Version: 12.2, Runtime API Version: 12.2
W0330 14:00:00.000000 12345 gpu_resources.cc:164] device: 0, cuDNN Version: 8.9.
PaddlePaddle works well on 1 GPU.
PaddlePaddle is installed successfully! Let's start deep learning with PaddlePaddle now.
```

### 8.5 閰嶇疆鐜鍙橀噺

鍒涘缓 `/opt/ocr/.env` 鏂囦欢锛?
```bash
cat > /opt/ocr/.env << 'EOF'
# 鏁版嵁搴撻厤缃紙淇敼瀵嗙爜锛侊級
DATABASE_URL=postgresql+asyncpg://ocruser:YourStrongPassword123!@localhost:5432/ocr_db

# Redis 閰嶇疆
REDIS_URL=redis://127.0.0.1:6379/0

# 鐩綍閰嶇疆
UPLOAD_DIR=/opt/ocr/uploads
CACHE_DIR=/opt/ocr/.cache

# OCR 閰嶇疆锛圚20 GPU锛?OCR_USE_GPU=true
OCR_DEVICE=gpu:0
OCR_LANG=ch

# 鍒濆鏁版嵁瀵煎叆閰嶇疆锛堝彲閫夛級
INIT_ARCHIVE_EXCEL_PATH=/opt/ocr/data/archive.xls
INIT_ARCHIVE_BATCH_ID=init_import
EOF
```

### 8.6 鍔犺浇鐜鍙橀噺

鍦?`.bashrc` 涓坊鍔犺嚜鍔ㄥ姞杞斤細

```bash
echo 'set -a; source /opt/ocr/.env; set +a' >> ~/.bashrc
source ~/.bashrc
```

---

## 9. 鍚庣鏈嶅姟閰嶇疆

### 9.1 鍒濆鍖栨暟鎹簱

```bash
cd /opt/ocr
source .venv/bin/activate

# 鍔犺浇鐜鍙橀噺
set -a; source .env; set +a

# 杩愯鏁版嵁搴撹縼绉伙紙濡傛灉鏈?Alembic锛?# alembic upgrade head

# 鎴栬€呴€氳繃 FastAPI 鍚姩鏃惰嚜鍔ㄥ垱寤鸿〃
python -c "
from app.database import engine, Base
import asyncio

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('鏁版嵁搴撹〃鍒涘缓瀹屾垚')

asyncio.run(init())
"
```

### 9.2 娴嬭瘯鍚庣鍚姩

```bash
cd /opt/ocr
source .venv/bin/activate
set -a; source .env; set +a

# 鎵嬪姩鍚姩娴嬭瘯
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 鐪嬪埌浠ヤ笅杈撳嚭琛ㄧず鎴愬姛锛?# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

鎸?`Ctrl+C` 鍋滄娴嬭瘯銆?
### 9.3 鍒涘缓 systemd 鏈嶅姟

```bash
sudo tee /etc/systemd/system/ocr.service << 'EOF'
[Unit]
Description=OCR Archive Recognition Service
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=ocruser
Group=ocruser
WorkingDirectory=/opt/ocr
Environment="PATH=/opt/ocr/.venv/bin:/usr/local/cuda-12.2/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/ocr/.env

# 鍚姩鍛戒护
ExecStart=/opt/ocr/.venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log

# 閲嶅惎绛栫暐
Restart=always
RestartSec=5

# 璧勬簮闄愬埗
LimitNOFILE=65535
LimitNPROC=65535

# 鏃ュ織
StandardOutput=append:/opt/ocr/logs/uvicorn.log
StandardError=append:/opt/ocr/logs/uvicorn.error.log

[Install]
WantedBy=multi-user.target
EOF
```

### 9.4 鍚姩鍚庣鏈嶅姟

```bash
# 閲嶆柊鍔犺浇 systemd
sudo systemctl daemon-reload

# 鍚姩鏈嶅姟
sudo systemctl start ocr

# 璁剧疆寮€鏈鸿嚜鍚?sudo systemctl enable ocr

# 鏌ョ湅鐘舵€?sudo systemctl status ocr
```

---

## 10. 鍓嶇鏋勫缓涓庨儴缃?
### 10.1 瀹夎 Node.js 20

```bash
# 浣跨敤 NodeSource 浠撳簱
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 楠岃瘉
node --version  # v20.x.x
npm --version   # 10.x.x
```

### 10.2 瀹夎 pnpm锛堟帹鑽愶級

```bash
npm --version
```

### 10.3 鏋勫缓鍓嶇

```bash
cd /opt/ocr/frontend

# 瀹夎渚濊禆
npm ci
# 鎴?npm install

# 閰嶇疆 API 鍦板潃锛堢敓浜х幆澧冿級
cat > .env.production << 'EOF'
VITE_API_BASE_URL=/api
EOF

# 鏋勫缓
npm run build
# 鎴?npm run build

# 鏋勫缓浜х墿鍦?dist 鐩綍
ls -la dist/
```

### 10.4 閮ㄧ讲鍓嶇闈欐€佹枃浠?
```bash
# 鍒涘缓 Nginx 闈欐€佹枃浠剁洰褰?sudo mkdir -p /var/www/ocr

# 澶嶅埗鏋勫缓浜х墿
sudo cp -r /opt/ocr/frontend/dist/* /var/www/ocr/

# 璁剧疆鏉冮檺
sudo chown -R www-data:www-data /var/www/ocr
```

---

## 11. Nginx 鍙嶅悜浠ｇ悊閰嶇疆

### 11.1 瀹夎 Nginx

```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 11.2 閰嶇疆 Nginx

```bash
sudo tee /etc/nginx/sites-available/ocr << 'EOF'
server {
    listen 80;
    server_name _;  # 鏇挎崲涓轰綘鐨勫煙鍚嶆垨 IP

    # 鍓嶇闈欐€佹枃浠?    root /var/www/ocr;
    index index.html;

    # Gzip 鍘嬬缉
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;

    # 鍓嶇璺敱锛圫PA锛?    location / {
        try_files $uri $uri/ /index.html;
    }

    # 鍚庣 API 浠ｇ悊
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 鏀寔
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 瓒呮椂璁剧疆锛圤CR 鍙兘鑰楁椂杈冮暱锛?        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        
        # 鏂囦欢涓婁紶澶у皬闄愬埗
        client_max_body_size 100M;
    }

    # 涓婁紶鏂囦欢璁块棶
    location /uploads/ {
        alias /opt/ocr/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 鍋ュ悍妫€鏌?    location /health {
        proxy_pass http://127.0.0.1:8000/api/health;
    }

    # 闈欐€佽祫婧愮紦瀛?    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF
```

### 11.3 鍚敤閰嶇疆

```bash
# 鍒涘缓绗﹀彿閾炬帴
sudo ln -sf /etc/nginx/sites-available/ocr /etc/nginx/sites-enabled/

# 鍒犻櫎榛樿閰嶇疆锛堝彲閫夛級
sudo rm -f /etc/nginx/sites-enabled/default

# 娴嬭瘯閰嶇疆
sudo nginx -t

# 閲嶆柊鍔犺浇
sudo systemctl reload nginx
```

---

## 12. SSL 璇佷功閰嶇疆锛堝彲閫夛級

### 12.1 浣跨敤 Let's Encrypt锛堥渶瑕佸煙鍚嶏級

```bash
# 瀹夎 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 鐢宠璇佷功锛堟浛鎹㈠煙鍚嶏級
sudo certbot --nginx -d your-domain.com

# 鑷姩缁湡娴嬭瘯
sudo certbot renew --dry-run
```

### 12.2 浣跨敤鑷鍚嶈瘉涔︼紙娴嬭瘯鐜锛?
```bash
# 鐢熸垚鑷鍚嶈瘉涔?sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/ocr-selfsigned.key \
    -out /etc/ssl/certs/ocr-selfsigned.crt \
    -subj "/CN=localhost"

# 鍦?Nginx 閰嶇疆涓坊鍔?SSL
# listen 443 ssl;
# ssl_certificate /etc/ssl/certs/ocr-selfsigned.crt;
# ssl_certificate_key /etc/ssl/private/ocr-selfsigned.key;
```

---

## 13. 鍒濆鏁版嵁瀵煎叆

### 13.1 鍑嗗褰掓。鏁版嵁鏂囦欢

```bash
# 鍒涘缓鏁版嵁鐩綍
mkdir -p /opt/ocr/data

# 涓婁紶褰掓。 Excel 鏂囦欢鍒?/opt/ocr/data/archive.xls
# 鍙互浣跨敤 scp 鎴?sftp锛?# scp archive.xls user@server:/opt/ocr/data/
```

### 13.2 鎵ц鍒濆瀵煎叆

```bash
cd /opt/ocr
source .venv/bin/activate
set -a; source .env; set +a

# 鏂瑰紡涓€锛氫娇鐢ㄧ幆澧冨彉閲?export INIT_ARCHIVE_EXCEL_PATH=/opt/ocr/data/archive.xls
export INIT_ARCHIVE_BATCH_ID=init_import
python init_archive_db.py

# 鏂瑰紡浜岋細浣跨敤鍛戒护琛屽弬鏁?python init_archive_db.py /opt/ocr/data/archive.xls

# 鏂瑰紡涓夛細浜や簰寮忥紙濡傛灉鑴氭湰鏀寔锛?python init_archive_db.py
```

### 13.3 楠岃瘉瀵煎叆缁撴灉

```bash
# 杩炴帴鏁版嵁搴?psql -h localhost -U ocruser -d ocr_db

# 鏌ヨ瀵煎叆璁板綍鏁?SELECT COUNT(*) FROM archive_records;

# 鏌ョ湅鍓嶅嚑鏉¤褰?SELECT id, filename, archive_no FROM archive_records LIMIT 5;

# 閫€鍑?\q
```

---

## 14. 鏈嶅姟楠岃瘉

### 14.1 妫€鏌ユ墍鏈夋湇鍔＄姸鎬?
```bash
# PostgreSQL
sudo systemctl status postgresql

# Redis
sudo systemctl status redis-server

# OCR 鍚庣
sudo systemctl status ocr

# Nginx
sudo systemctl status nginx
```

### 14.2 娴嬭瘯 API

```bash
# 鍋ュ悍妫€鏌?curl http://localhost:8000/api/health

# 搴旇繑鍥炵被浼硷細
# {"status": "ok", "database": "connected", "redis": "connected"}

# 閫氳繃 Nginx 璁块棶
curl http://localhost/api/health
```

### 14.3 娴嬭瘯 OCR 鍔熻兘

```bash
# 鍑嗗娴嬭瘯鍥剧墖
# 涓婁紶娴嬭瘯鏂囦欢
curl -X POST http://localhost/api/ocr/upload \
    -F "file=@/path/to/test-image.jpg"

# 鎴栧湪娴忚鍣ㄤ腑璁块棶鍓嶇鐣岄潰
# http://YOUR_SERVER_IP/
```

### 14.4 GPU 鐘舵€佺洃鎺?
```bash
# 鏌ョ湅 GPU 浣跨敤鎯呭喌
nvidia-smi

# 鎸佺画鐩戞帶锛堟瘡 2 绉掑埛鏂帮級
watch -n 2 nvidia-smi

# 鏌ョ湅 GPU 杩涚▼
nvidia-smi pmon -i 0
```

---

## 15. systemd 鏈嶅姟绠＄悊

### 15.1 甯哥敤鍛戒护

```bash
# 鍚姩鏈嶅姟
sudo systemctl start ocr

# 鍋滄鏈嶅姟
sudo systemctl stop ocr

# 閲嶅惎鏈嶅姟
sudo systemctl restart ocr

# 閲嶆柊鍔犺浇閰嶇疆锛堜笉涓柇鏈嶅姟锛?sudo systemctl reload ocr

# 鏌ョ湅鐘舵€?sudo systemctl status ocr

# 鏌ョ湅鏃ュ織
sudo journalctl -u ocr -f

# 寮€鏈鸿嚜鍚?sudo systemctl enable ocr

# 绂佺敤寮€鏈鸿嚜鍚?sudo systemctl disable ocr
```

### 15.2 鏈嶅姟渚濊禆绠＄悊

```bash
# 鏌ョ湅鏈嶅姟渚濊禆
systemctl list-dependencies ocr

# 鎸夐『搴忓惎鍔ㄦ墍鏈夌浉鍏虫湇鍔?sudo systemctl start postgresql redis-server ocr nginx
```

---

## 16. 鏃ュ織绠＄悊

### 16.1 鏃ュ織浣嶇疆

| 鏈嶅姟 | 鏃ュ織浣嶇疆 |
|------|----------|
| OCR 鍚庣 | `/opt/ocr/logs/uvicorn.log` |
| OCR 閿欒 | `/opt/ocr/logs/uvicorn.error.log` |
| Nginx 璁块棶 | `/var/log/nginx/access.log` |
| Nginx 閿欒 | `/var/log/nginx/error.log` |
| PostgreSQL | `/var/log/postgresql/postgresql-15-main.log` |
| Redis | `/var/log/redis/redis-server.log` |

### 16.2 鏌ョ湅鏃ュ織

```bash
# 瀹炴椂鏌ョ湅 OCR 鍚庣鏃ュ織
tail -f /opt/ocr/logs/uvicorn.log

# 鏌ョ湅鏈€杩?100 琛岄敊璇棩蹇?tail -100 /opt/ocr/logs/uvicorn.error.log

# 浣跨敤 journalctl
sudo journalctl -u ocr --since "1 hour ago"

# 鏌ョ湅 Nginx 閿欒
sudo tail -f /var/log/nginx/error.log
```

### 16.3 鏃ュ織杞浆閰嶇疆

```bash
sudo tee /etc/logrotate.d/ocr << 'EOF'
/opt/ocr/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ocruser ocruser
    sharedscripts
    postrotate
        systemctl reload ocr > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

## 17. 澶囦唤涓庢仮澶?
### 17.1 鏁版嵁搴撳浠?
```bash
# 鍒涘缓澶囦唤鐩綍
mkdir -p /opt/ocr/backups

# 澶囦唤鏁版嵁搴?pg_dump -h localhost -U ocruser -d ocr_db -F c -f /opt/ocr/backups/ocr_db_$(date +%Y%m%d_%H%M%S).dump

# 瀹氭椂澶囦唤锛堟坊鍔犲埌 crontab锛?crontab -e

# 姣忓ぉ鍑屾櫒 2 鐐瑰浠?0 2 * * * pg_dump -h localhost -U ocruser -d ocr_db -F c -f /opt/ocr/backups/ocr_db_$(date +\%Y\%m\%d).dump
```

### 17.2 鎭㈠鏁版嵁搴?
```bash
# 鎭㈠澶囦唤
pg_restore -h localhost -U ocruser -d ocr_db -c /opt/ocr/backups/ocr_db_20260330.dump
```

### 17.3 澶囦唤涓婁紶鏂囦欢

```bash
# 澶囦唤涓婁紶鐩綍
tar -czvf /opt/ocr/backups/uploads_$(date +%Y%m%d).tar.gz /opt/ocr/uploads/

# 鎭㈠
tar -xzvf /opt/ocr/backups/uploads_20260330.tar.gz -C /
```

---

## 18. 鎬ц兘浼樺寲

### 18.1 H20 GPU 浼樺寲

```bash
# 璁剧疆 GPU 鎸佷箙鍖栨ā寮忥紙鍑忓皯鍚姩寤惰繜锛?sudo nvidia-smi -pm 1

# 璁剧疆 GPU 璁＄畻妯″紡涓虹嫭鍗?sudo nvidia-smi -c 3

# 璁剧疆鍔熻€楅檺鍒讹紙鍙€夛紝榛樿 400W锛?# sudo nvidia-smi -pl 350
```

### 18.2 PostgreSQL 浼樺寲

缂栬緫 `/etc/postgresql/15/main/postgresql.conf`锛?
```conf
# 鍐呭瓨閰嶇疆锛堟牴鎹湇鍔″櫒鍐呭瓨璋冩暣锛?shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 256MB
maintenance_work_mem = 2GB

# 杩炴帴鏁?max_connections = 200

# WAL 閰嶇疆
wal_buffers = 64MB
checkpoint_completion_target = 0.9
```

```bash
sudo systemctl restart postgresql
```

### 18.3 Redis 浼樺寲

缂栬緫 `/etc/redis/redis.conf`锛?
```conf
# 鏈€澶у唴瀛?maxmemory 4gb

# 娣樻卑绛栫暐
maxmemory-policy allkeys-lru

# 绂佺敤 THP
# 闇€瑕佸湪绯荤粺绾у埆璁剧疆
```

```bash
# 绂佺敤閫忔槑澶ч〉
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
sudo systemctl restart redis-server
```

### 18.4 绯荤粺绾т紭鍖?
```bash
# 缃戠粶浼樺寲
sudo tee -a /etc/sysctl.conf << 'EOF'
# TCP 浼樺寲
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3
EOF

# 搴旂敤
sudo sysctl -p
```

---

## 19. 甯歌闂鎺掓煡

### Q1锛歯vidia-smi 鏄剧ず "No devices were found"

**鍘熷洜**锛氶┍鍔ㄦ湭姝ｇ‘瀹夎鎴?GPU 鏈璇嗗埆銆?
**瑙ｅ喅鏂规**锛?
```bash
# 妫€鏌?GPU 纭欢
lspci | grep -i nvidia

# 閲嶆柊瀹夎椹卞姩
sudo apt purge nvidia-*
sudo apt autoremove
sudo ubuntu-drivers autoinstall
sudo reboot
```

### Q2锛欳UDA 鐗堟湰涓嶅尮閰?
**鍘熷洜**锛氶┍鍔ㄦ敮鎸佺殑 CUDA 鐗堟湰涓庡畨瑁呯殑 Toolkit 涓嶄竴鑷淬€?
**瑙ｅ喅鏂规**锛?
```bash
# 鏌ョ湅椹卞姩鏀寔鐨?CUDA 鐗堟湰
nvidia-smi | grep "CUDA Version"

# 瀹夎鍖归厤鐨?CUDA Toolkit
# 渚嬪椹卞姩鏄剧ず CUDA 12.2锛屽垯瀹夎 cuda-toolkit-12-2
```

### Q3锛歅addlePaddle 鏃犳硶浣跨敤 GPU

**鍘熷洜**锛欳UDA/cuDNN 鐜閰嶇疆闂銆?
**瑙ｅ喅鏂规**锛?
```bash
# 妫€鏌ョ幆澧冨彉閲?echo $CUDA_HOME
echo $LD_LIBRARY_PATH

# 楠岃瘉 CUDA
nvcc --version

# 閲嶆柊瀹夎 paddlepaddle-gpu
pip uninstall paddlepaddle-gpu
pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/

# 娴嬭瘯
python -c "import paddle; print(paddle.device.get_device())"
```

### Q4锛歊edis 杩炴帴澶辫触

**鍘熷洜**锛歊edis 鏈惎鍔ㄦ垨閰嶇疆閿欒銆?
**瑙ｅ喅鏂规**锛?
```bash
# 妫€鏌?Redis 鐘舵€?sudo systemctl status redis-server

# 妫€鏌ョ鍙?ss -tlnp | grep 6379

# 娴嬭瘯杩炴帴
redis-cli ping

# 鏌ョ湅鏃ュ織
sudo tail -50 /var/log/redis/redis-server.log
```

### Q5锛歅ostgreSQL 杩炴帴琚嫆缁?
**鍘熷洜**锛氳璇侀厤缃垨缃戠粶闂銆?
**瑙ｅ喅鏂规**锛?
```bash
# 妫€鏌?PostgreSQL 鐘舵€?sudo systemctl status postgresql

# 妫€鏌ョ洃鍚?ss -tlnp | grep 5432

# 妫€鏌?pg_hba.conf 閰嶇疆
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep -v "^#"

# 娴嬭瘯杩炴帴
psql -h localhost -U ocruser -d ocr_db
```

### Q6锛歂ginx 502 Bad Gateway

**鍘熷洜**锛氬悗绔湇鍔℃湭杩愯鎴栫鍙ｉ敊璇€?
**瑙ｅ喅鏂规**锛?
```bash
# 妫€鏌ュ悗绔湇鍔?sudo systemctl status ocr

# 妫€鏌ョ鍙?ss -tlnp | grep 8000

# 鐩存帴娴嬭瘯鍚庣
curl http://localhost:8000/api/health

# 鏌ョ湅 Nginx 閿欒鏃ュ織
sudo tail -50 /var/log/nginx/error.log
```

### Q7锛歄CR 澶勭悊瓒呮椂

**鍘熷洜**锛氬ぇ鏂囦欢鎴?GPU 鍐呭瓨涓嶈冻銆?
**瑙ｅ喅鏂规**锛?
```bash
# 鏌ョ湅 GPU 鍐呭瓨浣跨敤
nvidia-smi

# 鍑忓皯骞跺彂 workers
# 缂栬緫 /etc/systemd/system/ocr.service
# 灏?--workers 4 鏀逛负 --workers 2

# 閲嶅惎鏈嶅姟
sudo systemctl daemon-reload
sudo systemctl restart ocr
```

### Q8锛氭ā鍨嬩笅杞藉け璐?
**鍘熷洜**锛氱綉缁滈棶棰樻垨 HuggingFace 璁块棶鍙楅檺銆?
**瑙ｅ喅鏂规**锛?
```bash
# 浣跨敤鐧惧害 BOS 婧愶紙宸插湪 config.py 涓厤缃級
export PADDLE_PDX_MODEL_SOURCE=bos

# 鎴栨墜鍔ㄤ笅杞芥ā鍨嬪埌缂撳瓨鐩綍
# 鍙傝€?PaddleOCR 瀹樻柟鏂囨。
```

### Q9锛氱鐩樼┖闂翠笉瓒?
**鍘熷洜**锛氭ā鍨嬬紦瀛樻垨涓婁紶鏂囦欢杩囧銆?
**瑙ｅ喅鏂规**锛?
```bash
# 妫€鏌ョ鐩樹娇鐢?df -h

# 鏌ョ湅澶ф枃浠?du -sh /opt/ocr/*
du -sh /opt/ocr/.cache/*

# 娓呯悊鏃ф棩蹇?sudo journalctl --vacuum-time=7d

# 娓呯悊鏃у浠?rm /opt/ocr/backups/ocr_db_*.dump
```

### Q10锛氬墠绔〉闈㈢┖鐧?
**鍘熷洜**锛氭瀯寤哄け璐ユ垨璺敱閰嶇疆閿欒銆?
**瑙ｅ喅鏂规**锛?
```bash
# 妫€鏌ュ墠绔枃浠?ls -la /var/www/ocr/

# 妫€鏌?index.html 鏄惁瀛樺湪
cat /var/www/ocr/index.html

# 閲嶆柊鏋勫缓
cd /opt/ocr/frontend
npm run build
sudo cp -r dist/* /var/www/ocr/

# 妫€鏌?Nginx 閰嶇疆
sudo nginx -t
```

---

## 20. 杩愮淮鍛戒护閫熸煡

### 20.1 鏈嶅姟绠＄悊

```bash
# 鍚姩鎵€鏈夋湇鍔?sudo systemctl start postgresql redis-server ocr nginx

# 鍋滄鎵€鏈夋湇鍔?sudo systemctl stop nginx ocr redis-server postgresql

# 閲嶅惎 OCR 鏈嶅姟
sudo systemctl restart ocr

# 鏌ョ湅鎵€鏈夋湇鍔＄姸鎬?sudo systemctl status postgresql redis-server ocr nginx
```

### 20.2 鏃ュ織鏌ョ湅

```bash
# OCR 鍚庣瀹炴椂鏃ュ織
tail -f /opt/ocr/logs/uvicorn.log

# Nginx 璁块棶鏃ュ織
sudo tail -f /var/log/nginx/access.log

# 绯荤粺鏃ュ織
sudo journalctl -f
```

### 20.3 GPU 鐩戞帶

```bash
# GPU 鐘舵€?nvidia-smi

# 鎸佺画鐩戞帶
watch -n 1 nvidia-smi

# GPU 杩涚▼
nvidia-smi pmon
```

### 20.4 鏁版嵁搴撴搷浣?
```bash
# 杩炴帴鏁版嵁搴?psql -h localhost -U ocruser -d ocr_db

# 澶囦唤
pg_dump -h localhost -U ocruser -d ocr_db -F c -f backup.dump

# 鎭㈠
pg_restore -h localhost -U ocruser -d ocr_db -c backup.dump
```

### 20.5 浠ｇ爜鏇存柊

```bash
cd /opt/ocr

# 鎷夊彇鏈€鏂颁唬鐮?git pull

# 鏇存柊渚濊禆
source .venv/bin/activate
pip install -r requirements.txt

# 閲嶆柊鏋勫缓鍓嶇
cd frontend && npm run build && sudo cp -r dist/* /var/www/ocr/ && cd ..

# 閲嶅惎鏈嶅姟
sudo systemctl restart ocr
sudo systemctl reload nginx
```

### 20.6 蹇€熻瘖鏂?
```bash
# 涓€閿鏌ユ墍鏈夋湇鍔?echo "=== PostgreSQL ===" && sudo systemctl is-active postgresql
echo "=== Redis ===" && sudo systemctl is-active redis-server
echo "=== OCR ===" && sudo systemctl is-active ocr
echo "=== Nginx ===" && sudo systemctl is-active nginx
echo "=== GPU ===" && nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv
echo "=== Disk ===" && df -h /opt/ocr
echo "=== API ===" && curl -s http://localhost:8000/api/health
```

---

## 闄勫綍 A锛氬畬鏁寸幆澧冨彉閲忓垪琛?
| 鍙橀噺鍚?| 璇存槑 | 绀轰緥鍊?|
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 杩炴帴瀛楃涓?| `postgresql+asyncpg://ocruser:password@localhost:5432/ocr_db` |
| `REDIS_URL` | Redis 杩炴帴瀛楃涓?| `redis://127.0.0.1:6379/0` |
| `UPLOAD_DIR` | 涓婁紶鏂囦欢鐩綍 | `/opt/ocr/uploads` |
| `CACHE_DIR` | 妯″瀷缂撳瓨鐩綍 | `/opt/ocr/.cache` |
| `OCR_USE_GPU` | 鏄惁浣跨敤 GPU | `true` |
| `OCR_DEVICE` | OCR 璁惧 | `gpu:0` |
| `OCR_LANG` | OCR 璇█ | `ch` |
| `INIT_ARCHIVE_EXCEL_PATH` | 鍒濆瀵煎叆 Excel 璺緞 | `/opt/ocr/data/archive.xls` |
| `INIT_ARCHIVE_BATCH_ID` | 鍒濆瀵煎叆鎵规 ID | `init_import` |

---

## 闄勫綍 B锛氱鍙ｄ娇鐢ㄦ眹鎬?
| 绔彛 | 鏈嶅姟 | 鍗忚 | 璇存槑 |
|------|------|------|------|
| 80 | Nginx | TCP | HTTP 鍏ュ彛 |
| 443 | Nginx | TCP | HTTPS 鍏ュ彛 |
| 8000 | Uvicorn | TCP | 鍚庣 API |
| 5432 | PostgreSQL | TCP | 鏁版嵁搴?|
| 6379 | Redis | TCP | 缂撳瓨 |

---

## 闄勫綍 C锛氭枃浠剁粨鏋?
```
/opt/ocr/
鈹溾攢鈹€ .venv/                 # Python 铏氭嫙鐜
鈹溾攢鈹€ .cache/                # 妯″瀷缂撳瓨
鈹溾攢鈹€ .env                   # 鐜鍙橀噺閰嶇疆
鈹溾攢鈹€ uploads/               # 涓婁紶鏂囦欢鐩綍
鈹溾攢鈹€ logs/                  # 鏃ュ織鐩綍
鈹?  鈹溾攢鈹€ uvicorn.log
鈹?  鈹斺攢鈹€ uvicorn.error.log
鈹溾攢鈹€ backups/               # 澶囦唤鐩綍
鈹溾攢鈹€ data/                  # 鏁版嵁鏂囦欢锛堝鍒濆瀵煎叆 Excel锛?鈹溾攢鈹€ app/                   # 鍚庣浠ｇ爜
鈹溾攢鈹€ frontend/              # 鍓嶇浠ｇ爜
鈹?  鈹斺攢鈹€ dist/              # 鍓嶇鏋勫缓浜х墿
鈹溾攢鈹€ config.py              # 閰嶇疆鏂囦欢
鈹溾攢鈹€ requirements.txt       # Python 渚濊禆
鈹斺攢鈹€ init_archive_db.py     # 鍒濆鏁版嵁瀵煎叆鑴氭湰
```

---

## 闄勫綍 D锛氬弬鑰冭祫鏂?
- [NVIDIA H20 浜у搧椤甸潰](https://www.nvidia.com/en-us/data-center/h20/)
- [CUDA Toolkit 涓嬭浇](https://developer.nvidia.com/cuda-downloads)
- [cuDNN 涓嬭浇](https://developer.nvidia.com/cudnn)
- [PaddlePaddle 瀹樻柟鏂囨。](https://www.paddlepaddle.org.cn/)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [FastAPI 瀹樻柟鏂囨。](https://fastapi.tiangolo.com/)
- [PostgreSQL 瀹樻柟鏂囨。](https://www.postgresql.org/docs/)
- [Redis 瀹樻柟鏂囨。](https://redis.io/docs/)
- [Nginx 瀹樻柟鏂囨。](https://nginx.org/en/docs/)

---

**鏂囨。缁撴潫**

> 濡傛湁闂锛岃妫€鏌ユ棩蹇楁垨鍙傝€?[甯歌闂鎺掓煡](#19-甯歌闂鎺掓煡) 绔犺妭銆?
