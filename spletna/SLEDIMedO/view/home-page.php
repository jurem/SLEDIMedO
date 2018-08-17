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
		<section>
			<div id="wrapper">
				<div class="title">
					<span style="color: #344E5C;">SLEDI</span><span style="color: #4AB19D;">Med</span><span style="color: #EFC958;">O</span>
				</div>
				<form>
					<div id="search-wrapper">
						<div id="search-area">
							<input type="text" id="search-input" onkeyup="showResult(this.value)">
						</div>
						<div id="search-icon">
							<!-- <span class="helper"></span> -->
							<i class="fa fa-search fa-search-icon fa-rotate-90"></i>
							<!--<img src="<?= IMAGES_URL . "/search-icon-w-f.png" ?>"></div>-->
						</div>
					</div>
					<div id="livesearch"></div>
				</form>
			</div>
		</section>
	</div>
	<!-- Footer -->
	<?php include("footer.php"); ?>
	<script type="text/javascript" src="<?= JS_URL . 'livesearch.js' ?>"></script>
	<script type="text/javascript" src="<?= JS_URL . 'script.js' ?>"></script>
</body>
</html>