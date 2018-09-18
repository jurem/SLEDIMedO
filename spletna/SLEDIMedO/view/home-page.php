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
				<form action="<?= BASE_URL . 'index.php/results' ?>">
					<div id="filter-div">
					<div id="filter-title-div">Filter virov : </div>
						<label class="checkbox-container">
	  						<input type="radio" name="filter" checked="checked" value="ALL">Vsi viri
							<span class="checkmark"></span>
						</label>

						<label class="checkbox-container">
	 						<input type="radio" name="filter" id="filter-radio" value="INTERREG">Interreg
	  						<span class="checkmark"></span>
						</label>
					</div>
					<div id="search-wrapper">
						<div id="search-area">
							<input type="text" name="search" id="search-input" onkeyup="showResult(this.value)">
						</div>
						<div id="search-icon" onclick="search()">
							<i class="fa fa-search fa-search-icon fa-rotate-90"></i>
						</div>
					</div>
				</form>
				<div id="livesearch"></div>
			</div>
		</section>
	</div>
	<!-- Footer -->
	<?php include("footer.php"); ?>
	<script type="text/javascript" src="<?= JS_URL . 'script.js' ?>"></script>
	<script type="text/javascript" src="<?= JS_URL . 'livesearch.js' ?>"></script>
</body>
</html>