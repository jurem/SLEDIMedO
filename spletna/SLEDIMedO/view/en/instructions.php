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
				<div class="pages-title">Site instructions</div>
				<div class="pages-content">
					<p>
					This website <b>SlediMedO</b> was created to help with the search of news about different projects funded or co-funded by the European union. The search engine uses scrappers and a database to search through various Slovenian media and news websites, included ones with basic information about a given project.<br>
					To begin your searching, click on the site 'Search' where you'll see a search bar into which you'll type your search query. You can use names of different projects or their acronyms or some key words about the project. The site will then return the results of the search, such as a main website of the project with the basic information of the project, as well as news articles from various news sites about this project. The database mostly includes projects from the Danube region.
					</p>
					<br><br>
					<p class="page-sub-title">EXAMPLE OF USE</p>
					<p>
					Below you can see an example of how to use the website, with the '' project. To find the news you type key words, acronyms or full project names. The site will return different news websites with news about the project as well as websites with basic information about the project.
					(Insert pic of use)
					</p>
				</div>
			</div>
		</section>
	</div>
	<?php include("footer.php"); ?>
	<script type="text/javascript" src="<?= JS_URL . 'script.js' ?>"></script>
</body>
</html>