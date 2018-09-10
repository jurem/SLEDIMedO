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
					To begin your searching, click on the site 'Search' where you'll see a search bar into which you'll type your search query. You can use names of different projects or their acronyms or some key words about the project. The search bar will display some projects that are related to your search query. If none of them apply, just press the search icon and the site will take you to all the related news. Each search result has the name of the article, publication date and the main text. Otherwise, you can also click on the link that will take you directly to the web page of a given news article.
					</p>
					<br><br>
					<p class="page-sub-title">EXAMPLE OF USE</p>
					<p>
					Below you can see an example of how to use the website, with the search query 'smart'. To find the news you type key words, acronyms or full project names. The site will show you some search results in a drop down menu, but if none of them are what you are searching for, just press enter and the site will take you to a subsite, where every article related to your search query is.
					<img src="../img/slika1.png" alt="Example 1"><br>
					In the next image we can see three selected search results. To proceed we can just choose one and click on it.
					<img src="../img/slika2.png" alt="Example 2"><br>
					The last picture shows the summary of the article as well as its date and direct link to the origin website of the article.
					<img src="../img/slika3.png" alt="Example 3"><br>
					</p>
				</div>
			</div>
		</section>
	</div>
	<?php include("footer.php"); ?>
	<script type="text/javascript" src="<?= JS_URL . 'script.js' ?>"></script>
</body>
</html>