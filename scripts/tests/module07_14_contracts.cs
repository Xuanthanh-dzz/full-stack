using System.Reflection;
using System.Runtime.ExceptionServices;
using SearchingDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var rng=new Random(714);for(int n=0;n<80;n++){var a=Enumerable.Range(0,n).Select(_=>rng.Next(-10,11)).Order().ToArray();for(int key=-12;key<=12;key++){int lower=Array.FindIndex(a,x=>x>=key);if(lower<0)lower=a.Length;Check(Call<int>("LowerBound",a,key)==lower,"linear lower oracle");int found=Call<int>("BinarySearch",a,key);Check(a.Contains(key)?found>=0 && a[found]==key:found==-1,"binary membership");}}
 }
}
