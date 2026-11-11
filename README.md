# DRILL-14

새 10마리가 45 km/h로 좌우 왕복 비행한다. `Boy.Run.do()`처럼 이동과 날갯짓에 `game_framework.frame_time`을 적용한다.

- 이미지: `bird_animation.png`의 14프레임.
- 날갯짓: 기본 1초 주기. 5번째 프레임부터 상승하고 11번째부터 하강한다.
- 상하 이동 폭: 최저점~최고점 15cm, 기존 축척으로 5pixel.
- 설정: `bird.py` 상단의 속력·주기·높이·출력 배율 상수.
- 요구사항과 검증 상태: [PRD.md](PRD.md).

프로젝트 폴더에서 실행한다. 기존 `game2d` 환경에 필요한 패키지가 설치되어 있다.

```powershell
conda run -n game2d python main.py
```

창을 열지 않는 자동 검증:

```powershell
conda run -n game2d python -m unittest discover -s tests -v
```

일반 Python 환경을 쓴다면 `requirements.txt`의 패키지가 필요하다. 이번 작업에서는 자동 검증 24개를 통과했으며, 사용자 지시에 따라 창 실행과 시각 확인은 수행하지 않았다.
