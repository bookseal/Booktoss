#!/bin/bash
# install-playwright.sh
# Linux 환경에서 Playwright 브라우저 및 의존성 설치 스크립트

set -e

echo "======================================"
echo "Playwright 설치 스크립트 시작"
echo "======================================"

# Python 환경 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되어 있지 않습니다."
    exit 1
fi

echo "✅ Python3 확인됨: $(python3 --version)"

# pip로 playwright 설치 (이미 requirements에 있지만 확인용)
echo ""
echo "📦 Playwright Python 패키지 확인 중..."
pip install playwright --quiet

# Chromium 브라우저 설치
echo ""
echo "🌐 Chromium 브라우저 설치 중..."
playwright install chromium

# 시스템 의존성 설치 (root 권한 필요)
echo ""
echo "📚 시스템 의존성 설치 중..."
echo "   (sudo 권한이 필요할 수 있습니다)"

# Ubuntu/Debian 계열
if command -v apt-get &> /dev/null; then
    playwright install-deps chromium
# CentOS/RHEL 계열
elif command -v yum &> /dev/null; then
    echo "⚠️  CentOS/RHEL 계열에서는 수동으로 의존성을 설치해야 할 수 있습니다."
    playwright install-deps chromium || echo "의존성 설치 실패 - 수동 설치 필요"
else
    echo "⚠️  지원되지 않는 배포판입니다. 수동으로 의존성을 설치하세요."
fi

echo ""
echo "======================================"
echo "✅ Playwright 설치 완료!"
echo ""
echo "사용법:"
echo "  - 기본 (headless 모드): streamlit run app.py"
echo "  - GUI 모드: HEADLESS=false streamlit run app.py"
echo "======================================"
