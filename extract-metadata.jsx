#target illustrator

function collectAndCategorizeTextLayers(doc) {
    var collectedTextLayer = doc.layers.add();
    collectedTextLayer.name = "Collected Text";

    var headerSize = 0;
    var subheaderSize = 0;
    var textLayers = [];

    function collectTextFramesAndSizes(layer) {
        for (var i = layer.textFrames.length - 1; i >= 0; i--) {
            var textFrame = layer.textFrames[i];
            var fontSize = textFrame.textRange.characterAttributes.size;
            textLayers.push({ frame: textFrame, size: fontSize });
            textFrame.moveToBeginning(collectedTextLayer);

            if (fontSize > headerSize) {
                subheaderSize = headerSize;
                headerSize = fontSize;
            } else if (fontSize > subheaderSize && fontSize < headerSize) {
                subheaderSize = fontSize;
            }
        }

        for (var j = layer.layers.length - 1; j >= 0; j--) {
            collectTextFramesAndSizes(layer.layers[j]);
        }
    }

    function categorizeAndRenameTextLayers() {
        var headerCount = 1;
        var subheaderCount = 1;
        var bodyCopyCount = 1;

        for (var i = 0; i < textLayers.length; i++) {
            var layer = textLayers[i];
            var name, count;
            var sizeDifferenceHeader = (layer.size / headerSize) * 100;
            var sizeDifferenceSubheader = (layer.size / subheaderSize) * 100;

            if (sizeDifferenceHeader >= 80) {
                name = "Header";
                count = headerCount++;
            } else if (sizeDifferenceSubheader >= 60) {
                name = "Subheader";
                count = subheaderCount++;
            } else {
                name = "Body Copy";
                count = bodyCopyCount++;
            }

            layer.frame.name = name + " " + count;
        }
    }

    for (var i = doc.layers.length - 1; i >= 0; i--) {
        var layer = doc.layers[i];
        if (layer !== collectedTextLayer) {
            collectTextFramesAndSizes(layer);
        }
    }

    categorizeAndRenameTextLayers();
}

if (app.documents.length > 0) {
    collectAndCategorizeTextLayers(app.activeDocument);
} else {
    alert("No document is open");
}
