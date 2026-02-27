"""쿼리 동의어 확장."""

ALIASES = {
    # 클라우드
    "AWS": "Amazon Web Services AWS",
    "GCP": "Google Cloud Platform GCP",
    "Azure": "Microsoft Azure",
    "NCP": "Naver Cloud Platform NCP 네이버클라우드",
    "KT": "KT Cloud KT클라우드",
    # 도메인
    "금융": "금융 은행 증권 보험 카드 핀테크",
    "공공": "공공 정부 지자체 공기업 공공기관",
    "제조": "제조 생산 공장 스마트팩토리 MES",
    "유통": "유통 리테일 이커머스 쇼핑",
    "의료": "의료 병원 헬스케어 바이오",
    "교육": "교육 에듀테크 학교 대학",
    "통신": "통신 텔레코 5G 네트워크",
    "에너지": "에너지 전력 발전 신재생",
    # 기술
    "AI": "AI 인공지능 머신러닝 딥러닝 ML",
    "빅데이터": "빅데이터 데이터분석 데이터레이크 데이터웨어하우스",
    "DevOps": "DevOps CI/CD 파이프라인 자동화",
    "쿠버네티스": "쿠버네티스 Kubernetes K8s 컨테이너",
    "MSP": "MSP 매니지드서비스 클라우드운영 운영대행",
    "마이그레이션": "마이그레이션 클라우드전환 리프트앤시프트",
    "보안": "보안 시큐리티 CSPM CWPP 제로트러스트",
    "IaC": "IaC Infrastructure as Code 테라폼 Terraform",
    # 서비스 유형
    "SI": "SI 시스템통합 시스템구축",
    "SM": "SM 시스템운영 시스템유지보수",
    "컨설팅": "컨설팅 ISP BPR 전략수립",
}


def expand_query(query: str) -> str:
    """쿼리에 포함된 키워드의 동의어를 확장.

    Args:
        query: 원본 쿼리 문자열

    Returns:
        확장된 쿼리 문자열
    """
    expanded_parts = [query]

    for keyword, expansion in ALIASES.items():
        if keyword.lower() in query.lower():
            # 원본 쿼리에 이미 포함된 부분은 제외하고 추가
            extra_terms = []
            for term in expansion.split():
                if term.lower() not in query.lower():
                    extra_terms.append(term)
            if extra_terms:
                expanded_parts.append(" ".join(extra_terms))

    return " ".join(expanded_parts)
