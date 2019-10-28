version 1.0

import "imported.wdl"

workflow test {
    input {
        String input1
        String input2
    }
    if (true) {
        call imported.echo {
            input:
        }
    }
    scatter (x in [1,2]) {
        call imported.sw {
            input:
        }
    }
    parameter_meta {
        input1: "The first input"
        input2: "The second input"
    }
    meta {
        WDL_AID: {
            exclude: ["echo.shouldBeExcluded"]
        }
        authors: {
            name: "Percy",
            email: "PercivalFredrickSteinVonMuselKlossowskiDeRolothe3rd@whitestone.net",
            organization: "Vox Machina"
        }
        author: "Whomever"
        email: "whatever@where-ever.meh"
        description: "Once upon a midnight dreary, while I pondered, weak and weary, over many a quant and curious volumne of forgotten lore. While I nodded, nearly napping, suddenly there came a tapping, as if some one gently rapping, rapping at my chamber door. \"'Tis some visitor,\" I muttered, \"Tapping at my chamber door. This it is and nothing more!\""
    }
}