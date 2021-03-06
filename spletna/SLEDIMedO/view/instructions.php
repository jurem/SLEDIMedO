<!DOCTYPE html>
<html lang="en-US">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width" />
	<link rel="stylesheet" type="text/css" href="<?= CSS_URL . "style.css" ?>">
	<title>SLEDIMedO</title>
</head>
<body>
	<div class="main-container">
		<?php include("header.php"); ?>
		<div class="gradient-line"></div>
		<section>
			<div class="page-container">
				<div class="pages-title">Navodila za uporabo strani</div>
				<div class="pages-content">
					<p>
					Spletna stran <b>SlediMedO</b> je bila ustvarjena za iskanje različnih novic o projektih financiranih s strani Evropske unije. Hkrati ustvarjen iskalnik poskrbi tudi, da se iščejo rezultati oziroma novice z različnih spletnih strani. Med temi stranmi so vključene tudi osnovne strani o določenem projektu ter različni slovenski spletni viri.<br>
					<br>
					Za uporabo kliknite na podstran 'Iskanje', kjer se vam bo prikazal okvir za vpis iskalnega niza. Za iskalni ukaz lahko vpišete imena različnih projektov, njihove kratice oziroma približke imen projektov. Iskalnik vam že ob takojšnjem pisanju predlaga določene novice ali projekte, ki se ujemajo z vašim iskalnim nizom. Tako lahko izberete med njimi, ali pa preprosto pritisnite tipko enter. Stran vam bo nato prikazala podstran, kjer bodo zbrani rezultati, ki se ujemajo z vašim iskalnim nizom. Vsak rezultat iskanja ima svoj naslov ter datum objave, hkrati pa, če kliknete na določen rezultat, vas stran preusmeri na podstran, kjer je zbrana novica, poleg tega pa lahko tudi direktno obiščete spletno stran, kjer je bila novica objavljena. Poleg tega iskalnik omogoča še osnovno filtriranje, torej, da novice razdeli na tiste, ki imajo izvor na Interreg spletni strani, ter na vse ostale.
					</p>
					<br><br>
					<p class="page-sub-title">PRIMER UPORABE</p>
					<p>
					Spodaj je prikazan primer uporabe spletna strani za iskalni niz 'smart'. V iskalni okvir vpišete ključne besede, spletna stran vam medtem prikaže nekaj potencialnih zadetkov, sicer pa vam nato na podstrani prikaže vse zadetke, ki se ujemajo z vašim iskalnim nizom. Poleg tega pa ima stran na voljo tudi filtriranje, pri čemer lahko izbirate med novicami, ki prihajajo iz vira Interreg, ali pa med vsemi ostalimi.<br>
					Na prvi sliki vidimo iskalnik ter predloge spletne strani, ki jih dobimo za dano ključno besedo, za filtriranje pa so izbrane samo novice z vira Interreg.
					<img class="sub-page-img" src="<?= IMAGES_URL . "/instructions/slika1.PNG" ?>"><br>
					Zatem vidimo tri zadetke oziroma novice, ki jih vrne iskalni niz. Da odpremo naslednjo stran, preprosto kliknemo na izbrano novico.
					<img class="sub-page-img" src="<?= IMAGES_URL . "/instructions/slika2.PNG" ?>"><br>
					Na zadnji sliki je prikazana izbrana novica. Pri tem lahko vidimo izbrani tekst novice, hkrati pa tudi datum objave novice in direktno povezavo na spletno stran, kjer je novica objavljena.
					<img class="sub-page-img" src="<?= IMAGES_URL . "/instructions/slika3.PNG" ?>"><br>
					</p>
				</div>
			</div>
		</section>
	</div>
	<?php include("footer.php"); ?>
	<script type="text/javascript" src="<?= JS_URL . 'script.js' ?>"></script>
</body>
</html>