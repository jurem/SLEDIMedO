#!/bin/bash
source ~/scraperTests/venv_scrapers/bin/activate

fArg=""
if [ $# -eq 1 ] && [ $1 == "-F" ] ; then
        fArg=$1
fi

python Scraper-ced-slovenia.py $fArg
python Scraper-dolenjskilist.py $fArg
python Scraper-eu-skladi.py $fArg
python Scraper-fgg-uni.py $fArg
python Scraper-fis-unm.py $fArg
python Scraper-geopark-idrija.py $fArg
python Scraper-gzs.py $fArg
python scraper_interreg.py $fArg
python Scraper-koper.py $fArg
python Scraper-litija.py $fArg
python Scraper-lokalno.py $fArg
python Scraper-mladipodjetnik.py $fArg
python Scraper-mojaobcina.py $fArg
python Scraper-novomesto.py $fArg
python Scraper-ntf-uni.py $fArg
python Scraper-pina.py $fArg
python Scraper-podjetniski-portal.py $fArg
python Scraper-podjetniskisklad.py $fArg
python Scraper-prostorisodelovanja.py $fArg
python Scraper-razvoj.py $fArg
python Scraper-rralur.py $fArg
python Scraper-skupnostobcin.py $fArg
python Scraper-startup.py $fArg
python Scraper-tovarnapodjemov.py $fArg
python Scraper-tp-lj.si.py $fArg
python Scraper-twitter.py $fArg
python Scraper-uni-lj.py $fArg
python Scraper-velenje.py $fArg
python Scraper-visit-idrija.py $fArg
python Scraper-vo-ka.py $fArg
python Scraper-zadnjenovice.py $fArg
python Scraper-zmos.py $fArg
python Scraper-zrsvn.py $fArg
python Scraper-cpi.py $fArg

deactivate
