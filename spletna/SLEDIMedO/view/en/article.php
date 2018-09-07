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
		<div id="gradient"></div>
		<section>
			<div class="page-container">
				<div class="article-title"><?= $article[0]["CAPTION"] ?></div>
				<div class="article-info clearfix">
					<div class="article-date"><i class="fa fa-calendar" id="calendar-img"></i><span id="date"><?= $article[0]["DATE"] ?></span></div>
					<div class="article-source">
						Source : <a href='<?= $article[0]["URL"] ?>' target="_blank"><?= $article[0]["SOURCE"] ?></a>
					</div>
				</div>
				<div class="article-contents"><?= $article[0]["CONTENTS"] ?></div>
	    	</div>
		</section>
	</div>
	<!-- Footer -->
	<?php include("footer.php"); ?>
	<script type="text/javascript" src="<?= JS_URL . 'script.js' ?>"></script>
</body>
</html>