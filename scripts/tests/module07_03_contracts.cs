using System.Reflection;
using System.Runtime.ExceptionServices;
using DynamicArrayDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var a=new SimpleDynamicArray<int>(1);var model=new List<int>();var rng=new Random(73);for(int i=0;i<500;i++){int op=rng.Next(4),v=rng.Next(20);if(op==0){a.Add(v);model.Add(v);}else if(op==1){int at=rng.Next(model.Count+1);a.Insert(at,v);model.Insert(at,v);}else if(op==2){Check(a.Remove(v)==model.Remove(v),"remove result");}else if(model.Count>0){int at=rng.Next(model.Count);a.RemoveAt(at);model.RemoveAt(at);}Check(a.Count==model.Count && a.Capacity>=a.Count && a.ToArray().SequenceEqual(model),"array model");}Throws<ArgumentOutOfRangeException>(()=>a.RemoveAt(a.Count));a.Add(99);var copy=a.ToArray();copy[0]=-1;Check(a[0]!=-1,"copy ownership");
 }
}
