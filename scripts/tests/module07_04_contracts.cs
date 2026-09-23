using System.Reflection;
using System.Runtime.ExceptionServices;
using LinkedListDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var a=new SimpleLinkedList<int>();var model=new List<int>();var rng=new Random(74);for(int i=0;i<500;i++){int v=rng.Next(10);switch(rng.Next(3)){case 0:a.AddFirst(v);model.Insert(0,v);break;case 1:a.AddLast(v);model.Add(v);break;default:Check(a.RemoveFirst(v)==model.Remove(v),"remove first result");break;}Check(a.Count==model.Count && a.Enumerate().SequenceEqual(model),"list model");Check(a.Contains(v)==model.Contains(v),"contains");}foreach(int v in model.ToArray())Check(a.RemoveFirst(v),"drain");a.AddLast(5);Check(a.Count==1 && a.Enumerate().Single()==5,"tail reset");
 }
}
