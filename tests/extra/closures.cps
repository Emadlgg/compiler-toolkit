function exterior(): integer {
    let x: integer = 10;

    function interior(): integer {
        return x;
    }

    return interior();
}

let resultado: integer = exterior();