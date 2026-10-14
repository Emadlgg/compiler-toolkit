func main:                             ; nivel 0, registro de 32 bytes
    enter 32
    t0 = newarray 3
    t0[0] = 10
    t0[1] = 20
    t0[2] = 30
    nums = t0
    t0 = nums[0]
    param t0
    call print, 1
    nums[1] = 25
    t0 = nums[1]
    param t0
    call print, 1
    t0 = nums[0]
    t1 = nums[2]
    t0 = t0 + t1
    param t0
    call print, 1
    t0 = newarray 2
    t1 = newarray 2
    t1[0] = 1
    t1[1] = 2
    t0[0] = t1
    t1 = newarray 2
    t1[0] = 3
    t1[1] = 4
    t0[1] = t1
    m = t0
    t0 = m[1]
    t0 = t0[0]
    param t0
    call print, 1
    t0 = m[0]
    t0[1] = 9
    t0 = m[0]
    t0 = t0[1]
    param t0
    call print, 1
    total = 0
    t0 = nums
    t1 = len t0
    t2 = 0
  L1:
    if t2 >= t1 goto L3
    n = t0[t2]
    total = total + n
    t2 = t2 + 1
    goto L1
  L3:
    param total
    call print, 1
    i = 0
  L4:
    if i >= 3 goto L5
    t0 = nums[i]
    t0 = t0 * 2
    nums[i] = t0
    i = i + 1
    goto L4
  L5:
    t0 = nums[2]
    param t0
    call print, 1
    t0 = nums
    t1 = len t0
    t2 = 0
  L6:
    if t2 >= t1 goto L8
    v = t0[t2]
    if v > 40 goto L8
    param v
    call print, 1
    t2 = t2 + 1
    goto L6
  L8:
    t0 = newarray 2
    t0[0] = "a"
    t0[1] = "b"
    ws = t0
    t0 = ws
    t1 = len t0
    t2 = 0
  L10:
    if t2 >= t1 goto L12
    w = t0[t2]
    param w
    call print, 1
    t2 = t2 + 1
    goto L10
  L12:
    halt
