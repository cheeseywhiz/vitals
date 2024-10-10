set -e

if [[ -z $VITALS_STATIC_FILES ]]; then
    echo VITALS_STATIC_FILES not set
    exit 1
fi

cp -r album-covers-original/* $VITALS_STATIC_FILES/album_cover/
