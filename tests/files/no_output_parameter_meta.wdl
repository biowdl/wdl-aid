version 1.0

workflow test {
    input {
        String A
    }
    output {
        File B = A
    }
    parameter_meta {
        A: "some text"
    }
}