#!/bin/bash
# Рендер своей доли роликов: shard.sh <номер> <всего>. Пропускает первые 21 карточку (их делает Мак).
set -u
cd "$(dirname "$0")"
N=$1; T=$2
SKIP="blood_vein cbc colono colono_prep ct_abd echo ecg fgds fna_thyroid fobt gallbladder holter iv_drip mammo mole ogtt stress_ecg tooth_out us_liver us_preg1 us_thyroid"
mkdir -p dist
i=0
LIST=$(cat batch.txt 2>/dev/null || ls ../../content/cards | sed 's/.json$//')
for id in $(echo $LIST | tr ' ' '\n' | sort); do
  [[ ! -f batch.txt && " $SKIP " == *" $id "* ]] && continue
  for lang in ru en kk es pt ar zh ja ko; do
    if (( i % T == N )); then
      echo "::group::$id $lang"
      if python3 build.py $id $lang && (cd proj_${id}_$lang && npx --yes hyperframes@0.8.119 render --quality looks --output ../raw.mp4 < /dev/null > render.log 2>&1); then
        ffmpeg -v error -y -i raw.mp4 -c:v libx264 -preset medium -crf 22 -pix_fmt yuv420p -c:a copy -movflags +faststart dist/${id}_$lang.mp4 && cp ${id}_$lang.srt dist/ && rm -rf raw.mp4 proj_${id}_$lang
        echo "OK $id $lang"
      else
        echo "FAIL $id $lang"; tail -20 proj_${id}_$lang/render.log 2>/dev/null
      fi
      echo "::endgroup::"
    fi
    i=$((i+1))
  done
done
ls dist | wc -l
