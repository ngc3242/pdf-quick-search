# Local Development Notes

## Production Site

**URL**: http://218.38.52.214:8081

---

## VPS Server Information

### SSH Connection
```bash
ssh root@218.38.52.214
```

### Server Details
- **Hostname**: emong112.cafe24.com
- **IP**: 218.38.52.214
- **Production Port**: 8081 (Nginx)
- **App Directory**: /var/www/pdf-search/
- **Backend Service**: pdf-search.service
- **Backend Port**: 5010 (internal)
- **Frontend**: Nginx serving static files

---

## 배포 방법 (CI/CD 자동 배포)

### 표준 배포 절차

```bash
# 1. 코드 수정 후 커밋
git add .
git commit -m "feat: 변경 내용 설명"

# 2. push하면 자동 배포
git push origin main

# 3. 배포 상태 확인 (선택)
gh run list --limit 1
```

**push하면 GitHub Actions가 자동으로:**
1. 서버에 SSH 접속
2. `git pull origin main` 실행
3. 백엔드 의존성 설치 (`pip install -r requirements.txt`)
4. 프론트엔드 빌드 (`npm install && npm run build`)
5. 권한 설정 및 서비스 재시작
6. Health check 확인

### 배포 상태 확인

```bash
# CLI로 확인
gh run list --limit 3

# 또는 웹에서 확인
# https://github.com/ngc3242/pdf-quick-search/actions
```

### 배포 로그 보기

```bash
# 최근 배포 로그 확인
gh run view --log
```

---

## 수동 배포 (CI/CD 실패 시)

### 전체 배포
```bash
ssh root@218.38.52.214 "cd /var/www/pdf-search && git pull origin main && cd backend && source venv/bin/activate && pip install -r requirements.txt && cd ../frontend && npm install && npm run build && cd .. && chown -R www-data:www-data . && systemctl restart pdf-search"
```

### 백엔드만 배포
```bash
ssh root@218.38.52.214 "cd /var/www/pdf-search && git pull origin main && systemctl restart pdf-search"
```

### 프론트엔드만 배포
```bash
ssh root@218.38.52.214 "cd /var/www/pdf-search && git pull origin main && cd frontend && npm run build"
```

---

## 서버 상태 확인

### 서비스 상태
```bash
ssh root@218.38.52.214 "systemctl status pdf-search"
```

### Health Check
```bash
ssh root@218.38.52.214 "curl -s http://127.0.0.1:5010/api/health"
# 정상: {"status":"ok"}
```

### 로그 확인
```bash
# 실시간 로그
ssh root@218.38.52.214 "journalctl -u pdf-search -f"

# 최근 100줄
ssh root@218.38.52.214 "journalctl -u pdf-search -n 100"
```

### 서비스 재시작
```bash
ssh root@218.38.52.214 "systemctl restart pdf-search"
```

---

## GitHub Secrets

CI/CD에 필요한 시크릿 (설정 완료):
- `VPS_HOST`: 218.38.52.214
- `VPS_USER`: root
- `VPS_SSH_KEY`: ED25519 deploy key (/root/.ssh/deploy_key)

시크릿 확인:
```bash
gh secret list
```


---

## MoAI-ADK Update Procedure

moai-adk 업데이트 명령어:

```bash
uv tool install moai-adk==X.X.X --force --upgrade && moai --version
```

Claude Code 재시작 후 버전이 자동 반영됨 (hook이 `moai --version` CLI 사용)

GitHub 릴리즈: https://github.com/modu-ai/moai-adk/releases



---

## 트러블슈팅

### CI/CD 실패 시
1. `gh run view --log`로 에러 확인
2. SSH로 직접 접속하여 수동 배포
3. 서버 로그 확인: `journalctl -u pdf-search -n 50`

### 서비스 시작 안 될 때
```bash
ssh root@218.38.52.214 "cd /var/www/pdf-search/backend && source venv/bin/activate && python -c 'from app import create_app; create_app()'"
```

### 권한 문제
```bash
ssh root@218.38.52.214 "chown -R www-data:www-data /var/www/pdf-search && chmod 700 /var/www/pdf-search/backend/.env"
```
