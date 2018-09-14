#!/bin/bash

fArg=""
if [ $# -eq 1 ] && [ $1 == "-F" ] ; then
        fArg=$1
fi

source ~/scraperTests/venv_scrapers/bin/activate

python scraper_24ur.py $fArg
python scraper_agen_rs.py $fArg
python scraper_amazon_eu.py $fArg
python scraper_dol_muzej.py $fArg
python scraper_e3.py $fArg
python scraper_elektroPrimorska.py $fArg
python scraper_essGov.py $fArg
python scraper_golea.py $fArg
python scraper_interreg.py $fArg
python scraper_iun.py $fArg
python scraper_ljnovice.py $fArg
python scraper_maribor24.py $fArg
python scraper_mddsz.py $fArg
python scraper_mizs_gov.py $fArg
python scraper_mop_gov.py $fArg
python scraper_nascas.py $fArg
python scraper_nasstik.py $fArg
python scraper_novaGorica.py $fArg
python scraper_obcinaIdrija.py $fArg
python scraper_obcinaLjubljana.py $fArg
python scraper_obcinaLjubljana2.py $fArg
python scraper_obcinaMaribor.py $fArg
python scraper_obcinaTolmin.py $fArg
python scraper_prc.py $fArg
python scraper_primorske.py $fArg
python scraper_primorskiVal.py $fArg
python scraper_regionalObala.py $fArg
python scraper_sazu.py $fArg
python scraper_siol.py $fArg
python scraper_turisticnaZveza.py $fArg
python scraper_velenjcan.py $fArg
python scraper_zdruzenje_obcin.py $fArg
python scraper_zrcSazu.py $fArg
python scraper_zvdks.py $fArg

deactivate
