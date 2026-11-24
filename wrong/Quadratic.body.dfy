{
  // Correct answer, unreasonable cost: a pointless full pass over the array on
  // every step makes this O(n^2). Nothing in either spec mentions running time.
  i := 0;
  while i < a.Length
    invariant 0 <= i <= a.Length
    invariant forall j :: 0 <= j < i ==> a[j] != key
  {
    var k := 0;
    while k < a.Length
      invariant 0 <= k <= a.Length
    {
      k := k + 1;
    }
    if a[i] == key { return; }
    i := i + 1;
  }
  i := -1;
}
