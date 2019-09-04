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
    }
}