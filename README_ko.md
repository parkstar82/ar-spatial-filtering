[🇺🇸 English](README.md)

# 📐 AR Spatial Filtering: View Frustum Optimization for R-tree

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Spatial Index](https://img.shields.io/badge/Spatial%20Index-R--tree-green)
![Augmented Reality](https://img.shields.io/badge/AR-View%20Frustum-orange)

> **"삼각형으로 세상을 보는데, 왜 사각형으로 검색하나요?"**
>
> **"Why search a Rectangle when you are looking through a Triangle?"**

---

## 1. 프로젝트 소개
이 프로젝트는 **증강현실(AR)** 애플리케이션의 공간 검색 효율을 극대화하기 위해, 2011년 발표된 연구 논문의 핵심 알고리즘을 파이썬으로 구현하고 시각화한 프로젝트입니다.

기존의 공간 데이터베이스(R-tree 등)가 사용하는 **최소 경계 사각형(MBR)** 기반 검색은 AR의 **시야각(View Frustum)** 특성을 반영하지 못해 불필요한 데이터를 과도하게 검색하는 비효율이 존재합니다. 본 프로젝트는 이를 해결하는 **삼각형 노드 필터링 기법**을 시뮬레이션하여 성능 차이를 증명합니다.

### 📚 기반 논문 정보
* [cite_start]**논문명**: [R-tree에서 GeoSpatial AR 응용을 위한 공간 필터링 기법](https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=JAKO201117148820644) [cite: 1]
* **원제**: Spatial Filtering Techniques for Geospatial AR Applications in R-tree
* [cite_start]**핵심 기여**: R-tree 인덱스 탐색 단계에서 단순 사각형 겹침(Overlap)뿐만 아니라, **시야각(삼각형)과의 기하학적 포함 관계**를 판별하여 탐색 범위를 획기적으로 줄임[cite: 15, 24].

---

## 2. 문제 정의: Dead Space (죽은 영역)
[cite_start]AR 애플리케이션은 사용자 위치에서 특정 각도(예: 63°)로 펼쳐지는 **삼각형(부채꼴) 영역**의 데이터를 필요로 합니다. [cite: 121, 252]
하지만 전통적인 R-tree 검색은 이 삼각형을 감싸는 **커다란 사각형(MBR)**을 기준으로 데이터를 가져옵니다.

* [cite_start]**Dead Space란?**: 시야각(삼각형) 밖이지만, 검색 사각형(MBR) 안에는 포함되는 영역입니다. [cite: 14, 23, 115]
* [cite_start]**영향**: 사용자가 보지도 않는 영역의 데이터를 검색하기 위해 불필요한 디스크 I/O와 연산 비용이 발생합니다. [cite: 116, 133]

---

## 3. 시각적 증명: 가지치기(Pruning)의 효과

본 시뮬레이션은 서울시의 '구(Gu) - 동(Dong) - 건물(Building)' 계층 구조와 유사한 **Depth-4 R-tree**를 생성하여 두 알고리즘의 탐색 경로를 비교했습니다.

* **검은색 선 (Black)**: 방문하지 않음 / 가지치기 당함 (탐색 비용 0)
* **초록색 선 (Green)**: 방문함 / 스캔됨 (I/O 비용 발생)

### 0. 기준 지도 (Baseline Map)
실험에 사용된 계층적 R-tree 데이터 구조입니다. 촘촘한 그물망은 말단 노드(건물)를 나타냅니다.
<div align="center">
  <img src="assets/00_baseline_clean.png" alt="Baseline Map" width="600"/>
</div>

### 🔍 알고리즘 비교 (Standard vs Optimized)

| 1. 기존 MBR 검색 (Standard Search) | 2. AR 삼각형 필터 (AR Triangle Filter) |
| :---: | :---: |
| ![Standard Search](assets/01_standard_clean.gif) | ![AR Filter Search](assets/02_ar_filter_clean.gif) |
| **작동 방식**: 파란색 삼각형을 감싸는 **파란색 점선 사각형(MBR)**을 기준으로 검색합니다.<br><br>**결과**: 사각형에 조금이라도 걸치는 상위 노드(구/동)는 무조건 방문합니다. 결과적으로 화면에 **거대한 초록색 사각형** 영역이 스캔됩니다.<br><br>**비효율**: 삼각형 밖의 초록색 영역은 실제로는 필요 없는 **낭비된 검색(Dead Space)**입니다. | **작동 방식**: **파란색 삼각형(시야각)** 자체와 겹치는지 정밀하게 검사합니다.<br><br>**결과**: 상위 노드(예: 인접한 동네)가 사각형 범위 내에 있더라도, 실제 시야각(삼각형)과 겹치지 않는다면 즉시 **탐색을 중단(Pruning)**합니다.<br><br>**효율성**: 초록색 영역이 부채꼴 모양으로 깔끔하게 떨어지며, 나머지 영역은 **검은색**으로 남아 I/O 비용이 발생하지 않았음을 증명합니다. |

---

## 4. 실행 방법 (How to Run)

이 프로젝트는 Python 3.10+ 환경에서 실행됩니다.

### 설치

```bash
# 저장소 복제
git clone [https://github.com/YOUR_USERNAME/ar-spatial-filtering.git](https://github.com/YOUR_USERNAME/ar-spatial-filtering.git)
cd ar-spatial-filtering

# 의존성 패키지 설치
pip install -r requirements.txt
````

### 시각화 생성

아래 명령어를 실행하면 `assets/` 폴더에 벤치마크 GIF 파일들이 생성됩니다.

```bash
python src/fast_visualizer.py
```

*Keywords: Python, R-tree, GIS, Augmented Reality, Spatial Indexing, Visualization, Matplotlib, PostGIS*
