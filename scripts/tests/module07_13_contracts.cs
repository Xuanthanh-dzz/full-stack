using System.Reflection;
using System.Runtime.ExceptionServices;
using SortingDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var rng=new Random(713);for(int n=0;n<100;n++){int[] input=Enumerable.Range(0,n).Select(_=>rng.Next(-10,11)).ToArray();var expected=input.ToArray();Array.Sort(expected);var insert=input.ToArray();Call<object?>("InsertionSort",insert);Check(insert.SequenceEqual(expected),"insertion oracle");var merged=Call<int[]>("MergeSort",input);Check(merged.SequenceEqual(expected),"merge oracle");}var source=new[]{3,1,2};Call<int[]>("MergeSort",source);Check(source.SequenceEqual(new[]{3,1,2}),"merge does not mutate");
 }
}
