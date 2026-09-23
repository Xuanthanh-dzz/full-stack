using System.Reflection;
using System.Runtime.ExceptionServices;
using HashTableDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var a=new EmailAddress(" A@EXAMPLE.COM ");var b=new EmailAddress("a@example.com");Check(a==b && a.GetHashCode()==b.GetHashCode(),"normalized equality");var map=new Dictionary<EmailAddress,int>{{a,7}};Check(map[b]==7,"hash lookup");Throws<ArgumentException>(()=>new EmailAddress(" "));var counts=Call<Dictionary<string,int>>("CountWords","Code code test");Check(counts["code"]==2 && counts["test"]==1,"word comparer");
 }
}
