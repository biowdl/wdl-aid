version 1.0

import "imported.wdl"

workflow test {
    input {
        String input1
        String input2 = ":p"
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
    output {
        String? output1 = "Life needs things to live."
        String output2 = "This one lacks a description."
        Array[File] output3 = ["1", "2"]
        Int output4 = 1
        Boolean output5 = false
    }
    parameter_meta {
        input1: "The first input"
        input2: "The second input"
        output1: "It does but it is blatenly obvious and simplistic."
        output3: {description: "A very descriptive description."}
        output4: {description: "This one has a category!", category: "category"}
    }
    meta {
        WDL_AID: {
            exclude: ["echo.shouldBeExcluded", "output5"]
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