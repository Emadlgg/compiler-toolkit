import { Animal } from "./Animal";

export class Perro : Animal {
    let edad: integer;

    function constructor() {
        this.edad = 3;
    }

    function ladrar(): void {
        print(10);
    }
}