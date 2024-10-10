set -e

if [[ -z $VITALS_STATIC_FILES ]]; then
    echo VITALS_STATIC_FILES not set
    exit 1
fi

mkdir $VITALS_STATIC_FILES/album_cover
