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
			<div class="page-container">
				<div class="pages-title">Rezultati iskanja</div>
				<?php if ($results): ?>
					<?php foreach ($results as $result): ?>
					<a href="<?= BASE_URL . 'index.php/article?id=' . $result['ID'] ?>">
					<div class="news">
						<div class="news-title"><?= $result["CAPTION"] ?></div>
						<div class="news-info">
							<div class="date"><i class="fa fa-calendar" id="calendar-img"></i><span id="date"><?= $result["DATE"] ?></span></div>
							<!-- <div class="date"><?= $result["DATE"] ?></div> -->
						</div>
						<div class="news-contents"><?php echo substr($result["CONTENTS"] , 0, 200) . " ... " ?></div>
					</div>
					</a>
	    			<?php endforeach; ?>
	    		<?php else: ?>
	    			<div id="not-found-message">Ni rezultatov.</div>
				<?php endif; ?>
	    	</div>
		</section>
	</div>
	<!-- Footer -->
	<?php include("footer.php"); ?>
	<script type="text/javascript" src="<?= JS_URL . 'script.js' ?>"></script>
</body>
</html>