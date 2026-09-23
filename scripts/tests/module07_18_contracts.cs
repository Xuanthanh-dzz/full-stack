using System.Reflection;
using System.Runtime.ExceptionServices;
using DataStructureSelectionDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var index=new ProductIndex();var rng=new Random(718);var products=Enumerable.Range(1,100).Select(i=>new Product(i,"sku"+i,"p"+i,rng.Next(30))).ToArray();foreach(var p in products)index.Add(p);foreach(int k in new[]{0,1,10,100,110}){var top=index.TopPopular(k);Check(top.Select(x=>x.Popularity).SequenceEqual(products.Select(x=>x.Popularity).OrderDescending().Take(k)),"topK sort oracle");Check(top.Select(x=>x.Id).Distinct().Count()==top.Count,"no duplicate items");}Throws<InvalidOperationException>(()=>index.Add(new(101,"SKU1","duplicate",999)));Check(index.FindById(101)==null && index.FindById(1)==products[0],"failed SKU add rollback");Throws<InvalidOperationException>(()=>index.Add(new(1,"new","duplicate id",0)));Check(!index.ContainsSku("new"),"failed ID add preserves SKU");Throws<ArgumentException>(()=>index.Add(new(102," ","bad",0)));Check(index.FindById(102)==null,"guard before mutation");
 }
}
