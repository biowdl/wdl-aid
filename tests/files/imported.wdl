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
}