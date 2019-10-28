version 1.0

workflow sw {
    input {
        String? workflowOptional
    }
}

task echo {
    input {
        String? taskOptional
        String? missingDescription
        String? shouldBeExcluded
    }
    command {
        echo ~{taskOptional} :p
    }
    parameter_meta {
        taskOptional: {description: "an optional input",
                       category:"advanced",
                       desc: "alternative description",
                       cat: "common"}
    }
    meta {
        authors: [{
            name: "Percy",
            email: "PercivalFredrickSteinVonMuselKlossowskiDeRolothe3rd@whitestone.net",
            organization: "Vox Machina"
        },{
            name: "'Caleb'",
            email: "c.widowghast@example.com",
            organization: "The Mighty Nein"
        }]
    }
}