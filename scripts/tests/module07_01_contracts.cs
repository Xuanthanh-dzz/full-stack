using System.Reflection;
using System.Runtime.ExceptionServices;
using BigODemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
for(int n=0;n<50;n++){var a=Enumerable.Range(0,n).ToArray();Check(Call<long>("LinearSearch",a,-1)==n,"miss comparisons");if(n>0)Check(Call<long>("LinearSearch",a,0)==1,"early exit");Check(Call<long>("EstimateOrderedPairOperations",n)==(long)n*n,"pair count");}Check(Call<long>("EstimateOrderedPairOperations",int.MaxValue)==4611686014132420609L,"wide multiply");
 }
}
