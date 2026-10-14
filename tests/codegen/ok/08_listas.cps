// Listas: creación, lectura y escritura por índice, listas anidadas y foreach
let nums: integer[] = [10, 20, 30];
print(nums[0]);
nums[1] = 25;
print(nums[1]);
print(nums[0] + nums[2]);

let m: integer[][] = [[1, 2], [3, 4]];
print(m[1][0]);
m[0][1] = 9;
print(m[0][1]);

let total: integer = 0;
foreach (n in nums) { total = total + n; }
print(total);

let i: integer = 0;
while (i < 3) {
    nums[i] = nums[i] * 2;
    i = i + 1;
}
print(nums[2]);

foreach (v in nums) {
    if (v > 40) { break; }
    print(v);
}

let ws: string[] = ["a", "b"];
foreach (w in ws) { print(w); }
