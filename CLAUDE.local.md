# Local Development Notes

## VPS Deployment Information

### SSH Connection
```bash
ssh root@218.38.52.214
```

### Server Details
- Hostname: emong112.cafe24.com
- App Directory: /var/www/pdf-search/
- Backend Service: pdf-search.service
- Backend Port: 5010

---

## CI/CD (GitHub Actions)

### 자동 배포
`main` 브랜치에 push하면 자동으로 배포됩니다.

```bash
git add .
git commit -m "your message"
git push origin main
# → GitHub Actions가 자동으로 서버에 배포
```

### GitHub Secrets (설정 완료)
- `VPS_HOST`: 218.38.52.214
- `VPS_USER`: root
- `VPS_SSH_KEY`: ED25519 deploy key

### 배포 상태 확인
GitHub → Actions 탭에서 확인 가능

---

## 수동 배포 (필요시)

**SSH로 직접 배포:**
```bash
ssh root@218.38.52.214 "cd /var/www/pdf-search && git pull && cd frontend && npm run build && systemctl restart pdf-search"
```

**상태 확인:**
```bash
ssh root@218.38.52.214 "systemctl status pdf-search"
ssh root@218.38.52.214 "curl -s http://127.0.0.1:5010/api/health"
```
