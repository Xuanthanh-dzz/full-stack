using System.Reflection;
using System.Runtime.ExceptionServices;
using StackQueueDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
foreach(string good in new[]{"","abc","([]{})","a(b[c]d)e"})Check(Call<bool>("IsBalanced",good),"balanced");foreach(string bad in new[]{"(",")","([)]","}{","(()"})Check(!Call<bool>("IsBalanced",bad),"unbalanced");Throws<ArgumentNullException>(()=>Call<bool>("IsBalanced",new object?[]{null}));
 }
}
