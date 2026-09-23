using System.Reflection;
using System.Runtime.ExceptionServices;
using RecursionDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
for(int n=0;n<=100;n++){long expected=(long)n*(n+1)/2;Check(Call<long>("SumRecursive",n)==expected && Call<long>("SumIterative",n)==expected,"sum formula");}Throws<ArgumentOutOfRangeException>(()=>Call<long>("SumRecursive",-1));Throws<ArgumentOutOfRangeException>(()=>Call<long>("SumIterative",-1));Throws<ArgumentOutOfRangeException>(()=>Call<long>("FactorialWithTrace",21,0));var output=Console.Out;try{Console.SetOut(TextWriter.Null);Check(Call<long>("FactorialWithTrace",20,0)==2432902008176640000L,"20 factorial");Check(Call<long>("FactorialWithTrace",0,0)==1,"zero factorial");}finally{Console.SetOut(output);}Check(Call<int>("FindMax",new[]{-5,-2,-8},0)==-2,"negative max");Throws<ArgumentException>(()=>Call<int>("FindMax",Array.Empty<int>(),0));
 }
}
