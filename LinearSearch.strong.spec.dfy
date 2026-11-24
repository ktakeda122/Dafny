// Strengthened spec: pins down WHICH index and WHICH negative value.
method LinearSearch(a: array<int>, key: int) returns (i: int)
  ensures -1 <= i < a.Length
  ensures 0 <= i ==> a[i] == key && forall j :: 0 <= j < i ==> a[j] != key
  ensures i == -1 ==> forall j :: 0 <= j < a.Length ==> a[j] != key
